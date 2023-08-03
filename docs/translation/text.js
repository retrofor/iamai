/**
 * @typedef {"en-US"} DefaultLocale
 * @typedef {DefaultLocale | "zh-CN" } Locale
 */

/** @type {Readonly<Record<Locale, string>>} */
export const languageMap = {
  "undefined": "English",
  "en-US": "English",
  "zh-CN": "简体中文",
};

/** @type {Readonly<Record<Locale, string>>} */
export const feedbackLinkMap = {
  "undefined": "Question? Give us feedback →",
  "en-US": "Question? Give us feedback →",
  "zh-CN": "有疑问？给我们反馈 →",
};

/** @type {Readonly<Record<Locale, string>>} */
export const editTextMap = {
  "undefined": "Edit this page on GitHub →",
  "en-US": "Edit this page on GitHub →",
  "zh-CN": "在 GitHub 上编辑本页 →",
};