/** 管理端可维护字典分组（与后端 MAINTAINABLE_DICT_TYPES 保持一致） */

export interface MaintainableDictMeta {
  dictType: string
  label: string
  description: string
}

export interface DictManageGroup {
  key: string
  title: string
  items: MaintainableDictMeta[]
}

export const DICT_MANAGE_GROUPS: DictManageGroup[] = [
  {
    key: 'appeal',
    title: '企业诉求配置',
    items: [
      {
        dictType: 'APPEAL_TYPE',
        label: '企业诉求类型',
        description: '用于管理端受理企业诉求时选择诉求分类，例如政策咨询、问题协调、投诉建议等。',
      },
      {
        dictType: 'APPEAL_REJECT_REASON',
        label: '诉求不予受理原因',
        description: '用于管理端对企业诉求执行不予受理时选择原因。',
      },
    ],
  },
  {
    key: 'gov-meeting',
    title: '政企约见配置',
    items: [
      {
        dictType: 'GOV_MEETING_TOPIC',
        label: '政企约见主题',
        description: '用于企业端发起约见时选择约见主题，例如政策咨询、审批协调、要素保障等。',
      },
      {
        dictType: 'GOV_MEETING_LEVEL',
        label: '政企约见层级',
        description: '用于企业端选择期望约见层级，管理端受理时选择后台研判层级。',
      },
      {
        dictType: 'GOV_MEETING_REJECT_REASON',
        label: '约见不予受理原因',
        description: '用于管理端对政企约见申请执行不予受理时选择原因。',
      },
    ],
  },
  {
    key: 'enterprise-region',
    title: '企业与区域配置',
    items: [
      {
        dictType: 'INDUSTRY_TYPE',
        label: '行业类型',
        description: '用于企业端提交诉求、政企约见时选择所属行业。',
      },
      {
        dictType: 'REGION',
        label: '区划',
        description: '用于企业端选择所属区划，管理端查询筛选。',
      },
    ],
  },
  {
    key: 'meeting-room',
    title: '共享会议室配置',
    items: [
      {
        dictType: 'MEETING_ROOM_TYPE',
        label: '会议室类型',
        description: '用于管理端维护会议室类型，企业端筛选会议室。',
      },
      {
        dictType: 'MEETING_ROOM_FACILITY',
        label: '会议室设施',
        description: '用于管理端维护会议室设施，企业端查看和筛选会议室。',
      },
      {
        dictType: 'ENTERPRISE_TYPE',
        label: '企业类型',
        description: '用于会议室申请材料规则按企业类型配置。',
      },
      {
        dictType: 'MATERIAL_TYPE',
        label: '材料类型',
        description: '用于会议室申请材料规则及后续材料扩展。',
      },
    ],
  },
  {
    key: 'common',
    title: '通用业务配置',
    items: [
      {
        dictType: 'URGENCY_LEVEL',
        label: '紧急程度',
        description: '用于企业诉求、政企约见表单中选择紧急程度。可维护名称和排序，编码保存后不建议修改。',
      },
    ],
  },
]

export const MAINTAINABLE_DICT_TYPES = DICT_MANAGE_GROUPS.flatMap(g => g.items.map(i => i.dictType))

export function getDictMeta(dictType: string): MaintainableDictMeta | undefined {
  for (const g of DICT_MANAGE_GROUPS) {
    const found = g.items.find(i => i.dictType === dictType)
    if (found) return found
  }
  return undefined
}

/** 默认选中第一个可维护字典 */
export const DEFAULT_DICT_TYPE = DICT_MANAGE_GROUPS[0].items[0].dictType
