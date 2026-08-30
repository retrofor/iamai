"""Append-only JSONL persistence for provisional harness Experiments."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator, cast

from ._experiment import (
    ExperimentPlan,
    ExperimentResult,
    _TrialSlot,
    _trajectory_spec,
)
from ._model import (
    FrozenJsonValue,
    Task,
    Trajectory,
    TrajectoryRecord,
    TrialResult,
    _configuration_hash,
    _thaw_json,
)
from ._replay import replay

EXPERIMENT_STORE_FORMAT_VERSION = "1"
MAX_JSONL_RECORD_BYTES = 16 * 1024 * 1024

_ACTIVE_WRITERS: set[Path] = set()
_ACTIVE_READERS: dict[Path, int] = {}
_ACTIVE_WRITERS_GUARD = threading.Lock()


def _lock_stream(stream: BinaryIO) -> None:
    stream.seek(0, os.SEEK_END)
    if stream.tell() == 0:
        stream.write(b"\0")
        stream.flush()
    stream.seek(0)
    if os.name == "nt":
        msvcrt = importlib.import_module("msvcrt")
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        return
    fcntl = importlib.import_module("fcntl")
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_stream(stream: BinaryIO) -> None:
    if os.name == "nt":
        msvcrt = importlib.import_module("msvcrt")
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        return
    fcntl = importlib.import_module("fcntl")
    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _lock_reader_stream(stream: BinaryIO) -> None:
    if os.name == "nt":
        msvcrt = importlib.import_module("msvcrt")
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            if not stream.writable():
                raise OSError("empty JSONL Store lock file is not readable on Windows")
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBRLCK, 1)
        return
    fcntl = importlib.import_module("fcntl")
    fcntl.flock(stream.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)


def _open_reader_lock(path: Path) -> BinaryIO | None:
    binary = getattr(os, "O_BINARY", 0)
    writable = False
    try:
        descriptor = os.open(
            path,
            (os.O_RDWR if os.name == "nt" else os.O_RDONLY) | binary,
        )
        writable = os.name == "nt"
    except FileNotFoundError:
        try:
            descriptor = os.open(
                path,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | binary,
                0o600,
            )
            writable = True
        except FileExistsError:
            descriptor = os.open(
                path,
                (os.O_RDWR if os.name == "nt" else os.O_RDONLY) | binary,
            )
            writable = os.name == "nt"
        except PermissionError:
            return None
    except PermissionError:
        if os.name != "nt":
            raise
        descriptor = os.open(path, os.O_RDONLY | binary)
        if os.fstat(descriptor).st_size == 0:
            os.close(descriptor)
            return None
    try:
        return os.fdopen(descriptor, "a+b" if writable else "rb", buffering=0)
    except BaseException:
        os.close(descriptor)
        raise


def _release_lock_stream(
    stream: BinaryIO,
    *,
    locked: bool,
    active_error: BaseException | None,
) -> None:
    cleanup_error: BaseException | None = None
    if locked:
        try:
            _unlock_stream(stream)
        except BaseException as error:
            cleanup_error = error
    try:
        stream.close()
    except BaseException as error:
        if cleanup_error is None:
            cleanup_error = error
        else:
            cleanup_error.add_note(f"also failed to close lock stream: {error!r}")
    if cleanup_error is None:
        return
    if active_error is not None:
        active_error.add_note(f"failed to release JSONL Store lock: {cleanup_error!r}")
        return
    raise cleanup_error


def _path_signature(path: Path) -> tuple[int, int, int, int] | None:
    try:
        metadata = path.stat()
    except FileNotFoundError:
        return None
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _decode_entry(raw_line: bytes, *, path: Path, line_number: int) -> Mapping[str, object]:
    if len(raw_line) > MAX_JSONL_RECORD_BYTES:
        raise ValueError(f"JSONL Store record is too large at {path}:{line_number}")
    try:
        value = json.loads(
            raw_line.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
        entry = _object(value, field=f"record at line {line_number}")
        if _canonical_json(entry) != raw_line:
            raise ValueError("record is not canonical JSON")
        return entry
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            f"invalid JSONL Store record at {path}:{line_number}: {error}"
        ) from error


def _validate_entry_chain(
    entries: list[Mapping[str, object]],
    *,
    path: Path,
) -> None:
    previous_digest: str | None = None
    for expected_sequence, entry in enumerate(entries):
        entry_digest = entry.get("entry_digest")
        entry_sequence = entry.get("entry_sequence")
        digest_payload = dict(entry)
        digest_payload.pop("entry_digest", None)
        if (
            isinstance(entry_sequence, bool)
            or not isinstance(entry_sequence, int)
            or entry_sequence != expected_sequence
            or entry.get("previous_entry_digest") != previous_digest
            or not isinstance(entry_digest, str)
            or entry_digest != _digest(digest_payload)
        ):
            raise ValueError(
                f"invalid JSONL Store entry chain at {path}:{expected_sequence + 1}"
            )
        previous_digest = entry_digest


def _trajectory_payload(trajectory: Trajectory) -> dict[str, object]:
    return {
        "format_version": trajectory.format_version,
        "trial_id": trajectory.trial_id,
        "task": {
            "id": trajectory.task.id,
            "input": _thaw_json(trajectory.task.input),
        },
        "seed": trajectory.seed,
        "configuration": _thaw_json(trajectory.configuration),
        "config_hash": trajectory.config_hash,
        "records": [
            {
                "sequence": record.sequence,
                "kind": record.kind,
                "payload": _thaw_json(record.payload),
            }
            for record in trajectory.records
        ],
    }


def _object(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"JSONL {field} must be an object")
    return value


def _trajectory_from_payload(value: object) -> Trajectory:
    payload = _object(value, field="Trajectory")
    task_payload = _object(payload.get("task"), field="Trajectory task")
    records_payload = payload.get("records")
    if not isinstance(records_payload, list):
        raise ValueError("JSONL Trajectory records must be an array")
    records: list[TrajectoryRecord] = []
    for raw_record in records_payload:
        record = _object(raw_record, field="Trajectory record")
        records.append(
            TrajectoryRecord(
                sequence=record.get("sequence"),  # type: ignore[arg-type]
                kind=record.get("kind"),  # type: ignore[arg-type]
                payload=cast(
                    Mapping[str, FrozenJsonValue],
                    _object(
                        record.get("payload"),
                        field="Trajectory record payload",
                    ),
                ),
            )
        )
    return Trajectory(
        format_version=payload.get("format_version"),  # type: ignore[arg-type]
        trial_id=payload.get("trial_id"),  # type: ignore[arg-type]
        task=Task(
            id=task_payload.get("id"),  # type: ignore[arg-type]
            input=cast(FrozenJsonValue, task_payload.get("input")),
        ),
        seed=payload.get("seed"),  # type: ignore[arg-type]
        configuration=cast(
            Mapping[str, FrozenJsonValue],
            _object(
                payload.get("configuration"),
                field="Trajectory configuration",
            ),
        ),
        config_hash=payload.get("config_hash"),  # type: ignore[arg-type]
        records=tuple(records),
    )


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class JsonlTrajectoryStore:
    """Persist one Experiment manifest and its terminal Trajectories as JSONL."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser().resolve()

    @property
    def path(self) -> Path:
        return self._path

    @contextmanager
    def _writer(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _ACTIVE_WRITERS_GUARD:
            if self.path in _ACTIVE_WRITERS:
                raise RuntimeError(
                    f"JSONL Store already has an active writer: {self.path}"
                )
            if _ACTIVE_READERS.get(self.path, 0):
                raise RuntimeError(
                    f"JSONL Store already has an active reader: {self.path}"
                )
            _ACTIVE_WRITERS.add(self.path)
        lock_path = self.path.with_name(f"{self.path.name}.lock")
        stream: BinaryIO | None = None
        locked = False
        try:
            descriptor = os.open(
                lock_path,
                os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0),
                0o600,
            )
            stream = os.fdopen(descriptor, "a+b", buffering=0)
            try:
                _lock_stream(stream)
            except OSError as error:
                raise RuntimeError(
                    f"JSONL Store already has an active writer: {self.path}"
                ) from error
            locked = True
            yield
        finally:
            active_error = sys.exception()
            try:
                if stream is not None:
                    _release_lock_stream(
                        stream,
                        locked=locked,
                        active_error=active_error,
                    )
            finally:
                with _ACTIVE_WRITERS_GUARD:
                    _ACTIVE_WRITERS.discard(self.path)

    @contextmanager
    def _reader(self) -> Iterator[None]:
        with _ACTIVE_WRITERS_GUARD:
            if self.path in _ACTIVE_WRITERS:
                raise RuntimeError(
                    f"JSONL Store already has an active writer: {self.path}"
                )
            _ACTIVE_READERS[self.path] = _ACTIVE_READERS.get(self.path, 0) + 1
        lock_path = self.path.with_name(f"{self.path.name}.lock")
        stream: BinaryIO | None = None
        locked = False
        try:
            stream = _open_reader_lock(lock_path)
            fallback_signature = None
            if stream is None:
                fallback_signature = _path_signature(lock_path)
                if fallback_signature is not None and fallback_signature[2] > 0:
                    stream = _open_reader_lock(lock_path)
                    if stream is None:
                        fallback_signature = _path_signature(lock_path)
            if stream is not None:
                try:
                    _lock_reader_stream(stream)
                except OSError as error:
                    raise RuntimeError(
                        f"JSONL Store already has an active writer: {self.path}"
                    ) from error
                locked = True
            yield
            if stream is None and _path_signature(lock_path) != fallback_signature:
                raise RuntimeError(
                    f"JSONL Store lock changed while being read: {self.path}"
                )
        finally:
            active_error = sys.exception()
            try:
                if stream is not None:
                    _release_lock_stream(
                        stream,
                        locked=locked,
                        active_error=active_error,
                    )
            finally:
                with _ACTIVE_WRITERS_GUARD:
                    remaining = _ACTIVE_READERS[self.path] - 1
                    if remaining:
                        _ACTIVE_READERS[self.path] = remaining
                    else:
                        del _ACTIVE_READERS[self.path]

    def _append(self, payload: Mapping[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        previous_digest: str | None = None
        sequence = 0
        if self.path.exists() and self.path.stat().st_size:
            content = self.path.read_bytes()
            if not content.endswith(b"\n"):
                raise ValueError(f"torn JSONL Store record at {self.path}")
            entries: list[Mapping[str, object]] = []
            for line_number, raw_line in enumerate(
                content[:-1].split(b"\n"),
                start=1,
            ):
                entries.append(
                    _decode_entry(
                        raw_line,
                        path=self.path,
                        line_number=line_number,
                    )
                )
            _validate_entry_chain(entries, path=self.path)
            sequence = len(entries)
            last_digest = entries[-1].get("entry_digest")
            if not isinstance(last_digest, str):
                raise AssertionError("validated JSONL entry digest was not a string")
            previous_digest = last_digest
        envelope = {
            **payload,
            "entry_sequence": sequence,
            "previous_entry_digest": previous_digest,
        }
        envelope["entry_digest"] = _digest(envelope)
        encoded = _canonical_json(envelope) + b"\n"
        if len(encoded) - 1 > MAX_JSONL_RECORD_BYTES:
            raise ValueError(f"JSONL Store record is too large: {len(encoded) - 1} bytes")
        descriptor = os.open(
            self.path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0),
            0o600,
        )
        with os.fdopen(descriptor, "ab", buffering=0) as stream:
            written = stream.write(encoded)
            if written != len(encoded):
                raise OSError("short JSONL write")
            os.fsync(stream.fileno())
        _fsync_directory(self.path.parent)

    def _sync_unlocked(self) -> None:
        flags = os.O_RDONLY if os.name != "nt" else os.O_RDWR
        descriptor = os.open(self.path, flags | getattr(os, "O_BINARY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _fsync_directory(self.path.parent)

    def repair_tail(self) -> bool:
        """Discard one unterminated final record after validating the complete prefix."""
        with self._writer():
            return self._repair_tail()

    def _repair_tail(self) -> bool:
        if not self.path.exists():
            return False
        content = self.path.read_bytes()
        if not content or content.endswith(b"\n"):
            return False
        prefix_end = content.rfind(b"\n") + 1
        prefix = content[:prefix_end]
        entries: list[Mapping[str, object]] = []
        raw_lines = prefix[:-1].split(b"\n") if prefix else []
        for line_number, raw_line in enumerate(raw_lines, start=1):
            entries.append(
                _decode_entry(
                    raw_line,
                    path=self.path,
                    line_number=line_number,
                )
            )
        _validate_entry_chain(entries, path=self.path)
        with self.path.open("r+b") as stream:
            stream.truncate(prefix_end)
            stream.flush()
            os.fsync(stream.fileno())
        _fsync_directory(self.path.parent)
        return True

    def _prepare(self, plan: ExperimentPlan) -> ExperimentResult:
        existing = self._load_unlocked()
        if existing is not None:
            if existing.plan_hash != plan.plan_hash:
                raise ValueError("JSONL Store contains a different Experiment plan")
            self._sync_unlocked()
            return existing
        self._append(
            {
                "record_type": "experiment.plan",
                "store_format_version": EXPERIMENT_STORE_FORMAT_VERSION,
                "plan": _thaw_json(plan._payload),
                "plan_hash": plan.plan_hash,
            }
        )
        prepared = self._load_unlocked()
        if prepared is None:
            raise RuntimeError("JSONL Store did not persist the Experiment plan")
        return prepared

    def _commit(
        self,
        plan: ExperimentPlan,
        slot: _TrialSlot,
        trajectory: Trajectory,
    ) -> None:
        planned_spec = plan.trial_specs[slot.variant][slot.position]
        spec_hash = plan._spec_hash(slot.variant, slot.position)
        if trajectory.trial_id != planned_spec.trial_id:
            raise ValueError("Trajectory does not match its Experiment slot")
        if _configuration_hash(_trajectory_spec(trajectory)) != spec_hash:
            raise ValueError("Trajectory provenance does not match its Experiment plan")
        replay(trajectory)
        trajectory_payload = _trajectory_payload(trajectory)
        self._append(
            {
                "record_type": "trajectory.committed",
                "store_format_version": EXPERIMENT_STORE_FORMAT_VERSION,
                "experiment_id": plan.experiment_id,
                "plan_hash": plan.plan_hash,
                "variant": slot.variant,
                "position": slot.position,
                "trial_id": trajectory.trial_id,
                "spec_hash": spec_hash,
                "trajectory": trajectory_payload,
                "trajectory_digest": _digest(trajectory_payload),
            }
        )

    def _start(self, plan: ExperimentPlan, slot: _TrialSlot) -> None:
        planned_spec = plan.trial_specs[slot.variant][slot.position]
        self._append(
            {
                "record_type": "trial.started",
                "store_format_version": EXPERIMENT_STORE_FORMAT_VERSION,
                "experiment_id": plan.experiment_id,
                "plan_hash": plan.plan_hash,
                "variant": slot.variant,
                "position": slot.position,
                "trial_id": planned_spec.trial_id,
                "spec_hash": plan._spec_hash(slot.variant, slot.position),
            }
        )

    def load(self) -> ExperimentResult | None:
        """Load and validate the Experiment results currently committed to this Store."""
        with _ACTIVE_WRITERS_GUARD:
            if self.path in _ACTIVE_WRITERS:
                raise RuntimeError(
                    f"JSONL Store already has an active writer: {self.path}"
                )
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        with self._reader():
            return self._load_unlocked()

    def _load_unlocked(self) -> ExperimentResult | None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        before = self.path.stat()
        content = self.path.read_bytes()
        after = self.path.stat()
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise RuntimeError(f"JSONL Store changed while being read: {self.path}")
        if not content.endswith(b"\n"):
            line_number = content.count(b"\n") + 1
            raise ValueError(
                f"torn JSONL Store record at {self.path}:{line_number}"
            )
        raw_lines = content[:-1].split(b"\n")
        if not raw_lines:
            return None
        entries: list[Mapping[str, object]] = []
        for line_number, raw_line in enumerate(raw_lines, start=1):
            entries.append(
                _decode_entry(
                    raw_line,
                    path=self.path,
                    line_number=line_number,
                )
            )
        _validate_entry_chain(entries, path=self.path)

        manifest = entries[0]
        if manifest.get("record_type") != "experiment.plan":
            raise ValueError("JSONL Store must start with an Experiment plan")
        if manifest.get("store_format_version") != EXPERIMENT_STORE_FORMAT_VERSION:
            raise ValueError("unsupported JSONL Store format version")
        plan_payload = _object(manifest.get("plan"), field="Experiment plan")
        stored_plan_hash = manifest.get("plan_hash")
        if not isinstance(stored_plan_hash, str):
            raise ValueError("JSONL Store Experiment plan hash is invalid")
        experiment_id = plan_payload.get("experiment_id")
        version = plan_payload.get("version")
        baseline = plan_payload.get("baseline")
        provenance = plan_payload.get("provenance")
        variants_payload = plan_payload.get("variants")
        if not isinstance(experiment_id, str) or not isinstance(version, str):
            raise ValueError("JSONL Store Experiment identity is invalid")
        if baseline is not None and not isinstance(baseline, str):
            raise ValueError("JSONL Store Experiment baseline is invalid")
        if not isinstance(provenance, Mapping):
            raise ValueError("JSONL Store Experiment provenance is invalid")
        if not isinstance(variants_payload, list) or not variants_payload:
            raise ValueError("JSONL Store Experiment variants are invalid")

        trial_specs: dict[str, tuple[Trajectory, ...]] = {}
        slots: dict[tuple[str, int], tuple[str, str]] = {}
        for raw_variant in variants_payload:
            variant_payload = _object(raw_variant, field="Experiment variant")
            variant = variant_payload.get("name")
            raw_trials = variant_payload.get("trials")
            if not isinstance(variant, str) or not isinstance(raw_trials, list):
                raise ValueError("JSONL Store Experiment variant is invalid")
            if variant in trial_specs:
                raise ValueError("JSONL Store Experiment variant is duplicate")
            specs: list[Trajectory] = []
            for raw_slot in raw_trials:
                slot_payload = _object(raw_slot, field="Experiment Trial slot")
                position = slot_payload.get("position")
                spec = _object(slot_payload.get("spec"), field="Experiment Trial spec")
                spec_hash = slot_payload.get("spec_hash")
                trial_id = spec.get("trial_id")
                if (
                    isinstance(position, bool)
                    or not isinstance(position, int)
                    or position != len(specs)
                    or not isinstance(trial_id, str)
                    or not isinstance(spec_hash, str)
                    or spec_hash
                    != _configuration_hash(cast(Mapping[str, FrozenJsonValue], spec))
                ):
                    raise ValueError("JSONL Store Experiment Trial slot is invalid")
                if "records" in spec:
                    raise ValueError("JSONL Store Experiment Trial spec is invalid")
                trajectory_spec = _trajectory_from_payload({**spec, "records": []})
                slots[(variant, position)] = (trial_id, spec_hash)
                specs.append(trajectory_spec)
            trial_specs[variant] = tuple(specs)

        plan = ExperimentPlan(
            experiment_id=experiment_id,
            version=version,
            trial_specs=trial_specs,
            baseline=baseline,
            provenance=cast(Mapping[str, FrozenJsonValue], provenance),
        )
        if plan.plan_hash != stored_plan_hash:
            raise ValueError("JSONL Store Experiment plan hash does not match")
        planned = dict(plan.planned_trial_ids)

        collected: dict[str, list[tuple[int, TrialResult]]] = {
            variant: [] for variant in planned
        }
        started_slots: set[tuple[str, int]] = set()
        committed_trial_ids: set[str] = set()
        for line_number, entry in enumerate(entries[1:], start=2):
            record_type = entry.get("record_type")
            if record_type not in {"trial.started", "trajectory.committed"}:
                raise ValueError(f"invalid JSONL Store record type at {self.path}:{line_number}")
            if entry.get("store_format_version") != EXPERIMENT_STORE_FORMAT_VERSION:
                raise ValueError("unsupported JSONL Store format version")
            if (
                entry.get("experiment_id") != experiment_id
                or entry.get("plan_hash") != stored_plan_hash
            ):
                raise ValueError("JSONL Store Trajectory does not match its Experiment")
            variant = entry.get("variant")
            position = entry.get("position")
            trial_id = entry.get("trial_id")
            if not isinstance(variant, str) or isinstance(position, bool) or not isinstance(
                position, int
            ):
                raise ValueError("JSONL Store Trajectory slot is invalid")
            declared_slot = slots.get((variant, position))
            if (
                declared_slot is None
                or not isinstance(trial_id, str)
                or declared_slot[0] != trial_id
                or entry.get("spec_hash") != declared_slot[1]
            ):
                raise ValueError("JSONL Store Trial record is unplanned")
            slot_key = (variant, position)
            if record_type == "trial.started":
                if slot_key in started_slots or trial_id in committed_trial_ids:
                    raise ValueError("JSONL Store Trial start is duplicate")
                started_slots.add(slot_key)
                continue
            if slot_key not in started_slots or trial_id in committed_trial_ids:
                raise ValueError("JSONL Store Trajectory is duplicate or was not started")
            trajectory_payload = _object(entry.get("trajectory"), field="Trajectory")
            if entry.get("trajectory_digest") != _digest(trajectory_payload):
                raise ValueError("JSONL Store Trajectory digest does not match")
            trajectory = _trajectory_from_payload(trajectory_payload)
            if _configuration_hash(_trajectory_spec(trajectory)) != declared_slot[1]:
                raise ValueError("JSONL Store Trajectory provenance does not match its plan")
            result = replay(trajectory)
            committed_trial_ids.add(trial_id)
            collected[variant].append((position, result))

        return ExperimentResult(
            plan=plan,
            results={
                variant: tuple(
                    result for _, result in sorted(variant_results, key=lambda item: item[0])
                )
                for variant, variant_results in collected.items()
            },
            started_trial_ids={
                variant: tuple(
                    trial_id
                    for position, trial_id in enumerate(trial_ids)
                    if (variant, position) in started_slots
                    and trial_id not in committed_trial_ids
                )
                for variant, trial_ids in planned.items()
            },
        )
