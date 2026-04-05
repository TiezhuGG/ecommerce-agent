from app.schemas.faq import FaqEntry


# FAQ 数据仍然先放在代码里，原因和商品目录一样：
# 先把“工具接口”和“业务边界”讲清楚，再上数据库，会更适合教学推进。
FAQ_ENTRIES: list[FaqEntry] = [
    FaqEntry(
        id="faq-return-001",
        topic="退换货",
        question="支持七天无理由退换货吗？",
        answer="除定制类商品外，大部分商品支持七天无理由退换货，商品需保持配件齐全且不影响二次销售。",
        source_label="售后政策 V1",
        keywords=["七天无理由", "退货", "换货", "退换货"],
    ),
    FaqEntry(
        id="faq-return-002",
        topic="退换货",
        question="拆封后还能退吗？",
        answer="若商品拆封后不影响二次销售，且符合平台售后规则，仍可申请售后；具体以商品页和平台规则为准。",
        source_label="售后政策 V1",
        keywords=["拆封", "退货", "售后", "影响二次销售"],
    ),
    FaqEntry(
        id="faq-invoice-001",
        topic="发票",
        question="可以开具发票吗？",
        answer="支持电子发票，提交订单后可在订单详情页申请开票。",
        source_label="发票说明 V1",
        keywords=["发票", "开票", "电子发票"],
    ),
    FaqEntry(
        id="faq-invoice-002",
        topic="发票",
        question="企业采购可以开专票吗？",
        answer="企业采购场景可根据平台规则申请增值税专用发票，实际开票能力以商品与店铺规则为准。",
        source_label="发票说明 V1",
        keywords=["专票", "企业采购", "增值税专用发票"],
    ),
    FaqEntry(
        id="faq-warranty-001",
        topic="保修",
        question="数码配件保修多久？",
        answer="不同品牌保修时长略有差异，默认提供 12 个月质保，具体以商品详情页和品牌规则为准。",
        source_label="质保说明 V1",
        keywords=["保修", "质保", "多久", "维修"],
    ),
    FaqEntry(
        id="faq-warranty-002",
        topic="保修",
        question="耳机进水还能保修吗？",
        answer="因进水、跌落等人为损坏导致的问题，通常不在常规质保范围内，建议参考品牌售后条款。",
        source_label="质保说明 V1",
        keywords=["进水", "保修", "人为损坏", "耳机"],
    ),
    FaqEntry(
        id="faq-delivery-001",
        topic="配送",
        question="一般多久能发货？",
        answer="常规现货商品一般会在 24 小时内完成发货，预售或缺货商品以页面说明为准。",
        source_label="配送说明 V1",
        keywords=["发货", "多久", "配送", "现货"],
    ),
    FaqEntry(
        id="faq-delivery-002",
        topic="配送",
        question="支持次日达或加急配送吗？",
        answer="部分地区和商品支持次日达或加急服务，具体以结算页展示的配送能力为准。",
        source_label="配送说明 V1",
        keywords=["次日达", "加急", "配送", "物流"],
    ),
]
