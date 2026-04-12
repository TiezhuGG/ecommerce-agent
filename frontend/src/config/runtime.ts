const devPanelsOverride = String(import.meta.env.VITE_SHOW_DEV_PANELS ?? "")
  .trim()
  .toLowerCase();

export const showDevPanels =
  devPanelsOverride === "true"
    ? true
    : devPanelsOverride === "false"
      ? false
      : import.meta.env.DEV;

export const devPanelsEntryLabel = import.meta.env.DEV
  ? "开发环境默认开放后台入口，后台路径现在由 vue-router 正式管理。"
  : "生产环境默认隐藏后台入口，只有显式开启 VITE_SHOW_DEV_PANELS 后才允许进入 /admin/*。";
