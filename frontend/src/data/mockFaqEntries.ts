import type { FaqEntry } from "../types/faq";

// FAQ 这一轮继续保留前端静态数据。
// 这样你可以明确看到：商品搜索已经进后端，FAQ 还停留在占位阶段，
// 方便后续单独把 FAQ 工具也迁到后端并写成下一轮迭代文档。
export const mockFaqEntries: FaqEntry[] = [
  {
    id: "faq-001",
    topic: "退换货",
    question: "支持七天无理由退换货吗？",
    answer:
      "除定制类商品外，大部分商品支持七天无理由退换货，商品需保持配件齐全且不影响二次销售。",
    sourceLabel: "售后政策 V1",
  },
  {
    id: "faq-002",
    topic: "发票",
    question: "可以开具发票吗？",
    answer: "支持电子发票，提交订单后可在订单详情页申请开票。",
    sourceLabel: "发票说明 V1",
  },
  {
    id: "faq-003",
    topic: "保修",
    question: "数码配件保修多久？",
    answer:
      "不同品牌保修时长略有差异，默认提供 12 个月质保，具体以商品详情页和品牌规则为准。",
    sourceLabel: "质保说明 V1",
  },
];
