import type { Product } from "../../types/catalog";


// 这里定义的是“接口返回契约”，而不是页面内部状态。
// 把它单独放在 contracts 目录里，后面你就能明显区分：
// 是后端字段变了，还是前端自己的状态设计变了。
export type ProductSearchResponse = {
  items: Product[];
  total: number;
  applied_filters: string[];
  available_categories: string[];
  available_brands: string[];
};
