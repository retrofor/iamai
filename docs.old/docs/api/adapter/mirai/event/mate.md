# iamai.adapter.mirai.event.mate

默认不会被传播的特殊事件。

## *class* `MateEvent`(self, adapter, **data) {#MateEvent}

Bases: `iamai.adapter.mirai.event.base.MiraiEvent`

默认不会被传播的特殊事件

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

## *class* `BotEvent`(self, adapter, **data) {#BotEvent}

Bases: `iamai.adapter.mirai.event.mate.MateEvent`

Bot 自身事件

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **qq** (*int*)

## *class* `BotOnlineEvent`(self, adapter, **data) {#BotOnlineEvent}

Bases: `iamai.adapter.mirai.event.mate.BotEvent`

Bot 登录成功

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **type** (*Literal['BotOnlineEvent']*)

## *class* `BotOfflineEventActive`(self, adapter, **data) {#BotOfflineEventActive}

Bases: `iamai.adapter.mirai.event.mate.BotEvent`

Bot 主动离线

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **type** (*Literal['BotOfflineEventActive']*)

## *class* `BotOfflineEventForce`(self, adapter, **data) {#BotOfflineEventForce}

Bases: `iamai.adapter.mirai.event.mate.BotEvent`

Bot 被挤下线

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **type** (*Literal['BotOfflineEventForce']*)

## *class* `BotOfflineEventDropped`(self, adapter, **data) {#BotOfflineEventDropped}

Bases: `iamai.adapter.mirai.event.mate.BotEvent`

Bot 被服务器断开或因网络问题而掉线

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **type** (*Literal['BotOfflineEventDropped']*)

## *class* `BotReloginEvent`(self, adapter, **data) {#BotReloginEvent}

Bases: `iamai.adapter.mirai.event.mate.BotEvent`

Bot 主动重新登录

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **type** (*Literal['BotReloginEvent']*)

## *class* `CommandExecutedEvent`(self, adapter, **data) {#CommandExecutedEvent}

Bases: `iamai.adapter.mirai.event.mate.MateEvent`

命令被执行

- **Arguments**

  - **adapter** (*~T_Adapter*) - 产生此事件的适配器对象。

  - ****data** (*Any*) - 事件数据。

- **Attributes**

  - **type** (*Literal['CommandExecutedEvent']*)

  - **name** (*str*)

  - **friend** (*Optional[iamai.adapter.mirai.event.base.FriendInfo]*)

  - **member** (*Optional[iamai.adapter.mirai.event.base.GroupMemberInfo]*)

  - **args** (*List[Any]*)