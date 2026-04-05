import type { Product } from "../../types/catalog";

// 这里定义的是“接口响应契约”，而不是前端页面内部状态。
// 把它单独放出来的好处是：后续如果后端字段变化，我们能快速定位
// 是“接口契约变了”，还是“页面内部状态设计变了”。
export type ProductSearchResponse = {
  items: Product[];
  total: number;
  applied_filters: string[];
  available_categories: string[];
  available_brands: string[];
};
