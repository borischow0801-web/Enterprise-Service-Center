<template>
  <div class="dict-manage">
    <div class="page-header">
      <h2>字典管理</h2>
      <span class="page-hint">仅维护业务配置类字典，系统状态类字典不在此页面显示</span>
    </div>

    <el-container class="dict-layout">
      <el-aside width="240px" class="dict-aside">
        <el-menu
          :default-active="currentDictType"
          class="dict-menu"
          @select="handleMenuSelect"
        >
          <el-sub-menu v-for="group in DICT_MANAGE_GROUPS" :key="group.key" :index="group.key">
            <template #title>{{ group.title }}</template>
            <el-menu-item
              v-for="item in group.items"
              :key="item.dictType"
              :index="item.dictType"
            >
              {{ item.label }}
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <el-main class="dict-main">
        <template v-if="currentMeta">
          <div class="dict-panel-header">
            <div class="dict-panel-title">
              <h3>{{ currentMeta.label }}</h3>
              <el-tag type="info" size="small">{{ currentMeta.dictType }}</el-tag>
            </div>
            <p class="dict-panel-desc">{{ currentMeta.description }}</p>
            <div class="dict-panel-actions">
              <el-form :model="filter" inline class="filter-inline">
                <el-form-item label="编码">
                  <el-input v-model="filter.dictCode" placeholder="筛选编码" clearable style="width:130px" />
                </el-form-item>
                <el-form-item label="名称">
                  <el-input v-model="filter.dictLabel" placeholder="筛选名称" clearable style="width:130px" />
                </el-form-item>
                <el-form-item label="状态">
                  <el-select v-model="filter.enabled" placeholder="全部" clearable style="width:90px">
                    <el-option label="启用" :value="1" />
                    <el-option label="停用" :value="0" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleSearch">查询</el-button>
                  <el-button @click="handleResetFilter">重置</el-button>
                </el-form-item>
              </el-form>
              <el-button type="primary" @click="openForm()">新增字典项</el-button>
            </div>
          </div>

          <el-card shadow="never" class="table-card">
            <el-table :data="list" v-loading="loading" stripe>
              <el-table-column prop="dictCode" label="字典编码" width="160" show-overflow-tooltip />
              <el-table-column prop="dictLabel" label="字典名称" min-width="140" />
              <el-table-column prop="dictValue" label="字典值" width="130" show-overflow-tooltip />
              <el-table-column prop="sortNo" label="排序" width="70" align="center" />
              <el-table-column label="启用状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.enabled === 1 ? 'success' : 'info'" size="small">
                    {{ row.enabled === 1 ? '启用' : '停用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="parentCode" label="父级编码" width="120" show-overflow-tooltip />
              <el-table-column prop="extraJson" label="扩展配置" min-width="100" show-overflow-tooltip />
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openForm(row)">编辑</el-button>
                  <el-button
                    link
                    :type="row.enabled === 1 ? 'warning' : 'success'"
                    @click="handleToggle(row)"
                  >{{ row.enabled === 1 ? '停用' : '启用' }}</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="pagination-wrap">
              <el-pagination
                v-model:current-page="pageNo"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[20, 50, 100]"
                layout="total, sizes, prev, pager, next"
                @change="fetchList"
              />
            </div>
          </el-card>
        </template>
      </el-main>
    </el-container>

    <el-dialog
      v-model="formVisible"
      :title="editingId ? '编辑字典项' : '新增字典项'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-alert
        v-if="!editingId"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom:12px"
      >
        字典编码建议使用英文大写下划线，保存后不建议修改。
      </el-alert>
      <el-alert
        v-else
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom:12px"
      >
        已使用的编码不建议修改，否则可能影响历史数据展示。
      </el-alert>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="字典类型">
          <el-input :model-value="currentDictType" disabled />
        </el-form-item>
        <el-form-item label="字典编码" prop="dictCode">
          <el-input v-model="form.dictCode" placeholder="如 POLICY_CONSULT" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="字典名称" prop="dictLabel">
          <el-input v-model="form.dictLabel" />
        </el-form-item>
        <el-form-item label="字典值">
          <el-input v-model="form.dictValue" placeholder="可选，默认可与编码相同" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortNo" :min="0" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-radio-group v-model="form.enabled">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="父级编码">
          <el-input v-model="form.parentCode" placeholder="可选" />
        </el-form-item>
        <el-form-item label="扩展JSON">
          <el-input v-model="form.extraJson" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  listDictionaries, createDictionary, updateDictionary, toggleDictionaryStatus,
  type DictionaryItem,
} from '@/api/dictionary'
import { DICT_MANAGE_GROUPS, DEFAULT_DICT_TYPE, getDictMeta } from '@/constants/dictManage'

const currentDictType = ref(DEFAULT_DICT_TYPE)
const currentMeta = computed(() => getDictMeta(currentDictType.value))

const loading = ref(false)
const submitting = ref(false)
const list = ref<DictionaryItem[]>([])
const total = ref(0)
const pageNo = ref(1)
const pageSize = ref(50)
const formVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const filter = reactive({
  dictCode: '',
  dictLabel: '',
  enabled: undefined as number | undefined,
})

const form = reactive({
  dictCode: '',
  dictLabel: '',
  dictValue: '',
  sortNo: 0,
  enabled: 1,
  parentCode: '',
  extraJson: '',
})

const formRules: FormRules = {
  dictCode: [{ required: true, message: '请输入字典编码', trigger: 'blur' }],
  dictLabel: [{ required: true, message: '请输入字典名称', trigger: 'blur' }],
}

function handleMenuSelect(dictType: string) {
  if (!getDictMeta(dictType)) return
  if (dictType === currentDictType.value) return
  currentDictType.value = dictType
  pageNo.value = 1
  filter.dictCode = ''
  filter.dictLabel = ''
  filter.enabled = undefined
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const res = await listDictionaries({
      dictType: currentDictType.value,
      dictCode: filter.dictCode || undefined,
      dictLabel: filter.dictLabel || undefined,
      enabled: filter.enabled,
      pageNo: pageNo.value,
      pageSize: pageSize.value,
    })
    list.value = res.records || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pageNo.value = 1
  fetchList()
}

function handleResetFilter() {
  filter.dictCode = ''
  filter.dictLabel = ''
  filter.enabled = undefined
  pageNo.value = 1
  fetchList()
}

function openForm(row?: DictionaryItem) {
  editingId.value = row?.id ?? null
  if (row) {
    Object.assign(form, {
      dictCode: row.dictCode,
      dictLabel: row.dictLabel,
      dictValue: row.dictValue || '',
      sortNo: row.sortNo,
      enabled: row.enabled,
      parentCode: row.parentCode || '',
      extraJson: row.extraJson || '',
    })
  } else {
    Object.assign(form, {
      dictCode: '', dictLabel: '', dictValue: '',
      sortNo: 0, enabled: 1, parentCode: '', extraJson: '',
    })
  }
  formVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      dictType: currentDictType.value,
      dictCode: form.dictCode,
      dictLabel: form.dictLabel,
      dictValue: form.dictValue || form.dictCode,
      sortNo: form.sortNo,
      enabled: form.enabled,
      parentCode: form.parentCode || undefined,
      extraJson: form.extraJson || undefined,
    }
    if (editingId.value) {
      await updateDictionary(editingId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createDictionary(payload)
      ElMessage.success('新增成功')
    }
    formVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

async function handleToggle(row: DictionaryItem) {
  const enabled = row.enabled === 1 ? 0 : 1
  const action = enabled === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定${action}字典项「${row.dictLabel}」吗？`, '确认', { type: 'warning' })
  } catch { return }
  await toggleDictionaryStatus(row.id, enabled)
  ElMessage.success(enabled === 1 ? '已启用' : '已停用')
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped>
.dict-manage { min-height: calc(100vh - 120px); }
.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}
.page-header h2 { margin: 0; font-size: 18px; }
.page-hint { color: #909399; font-size: 13px; }
.dict-layout {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: #fff;
  min-height: 560px;
}
.dict-aside {
  border-right: 1px solid #ebeef5;
  background: #fafafa;
}
.dict-menu { border-right: none; background: transparent; }
.dict-main { padding: 16px 20px; }
.dict-panel-header { margin-bottom: 12px; }
.dict-panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.dict-panel-title h3 { margin: 0; font-size: 16px; }
.dict-panel-desc {
  margin: 0 0 12px;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}
.dict-panel-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}
.filter-inline { margin: 0; }
.filter-inline :deep(.el-form-item) { margin-bottom: 0; }
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
