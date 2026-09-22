<template>
  <div class="admin-user-manage">
    <div class="page-header">
      <h2>管理员管理</h2>
      <span class="page-hint">
        统一身份认证（BSPPLUS）只负责核实账号密码；这里维护的角色/区划/数据范围才决定登录后能看什么、能做什么
      </span>
    </div>

    <el-card shadow="never" class="table-card">
      <el-form :model="filter" inline class="filter-inline">
        <el-form-item label="账号">
          <el-input v-model="filter.username" placeholder="按账号筛选" clearable style="width:160px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" placeholder="全部" clearable style="width:110px">
            <el-option label="启用" value="ACTIVE" />
            <el-option label="禁用" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filter.roleCode" placeholder="全部" clearable style="width:180px">
            <el-option v-for="r in ADMIN_ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
        <el-form-item style="margin-left: auto">
          <el-button type="primary" @click="openForm()">新增管理员</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="username" label="账号" width="140" show-overflow-tooltip />
        <el-table-column prop="realName" label="姓名" width="110" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column label="BSP 绑定状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.bspUserId ? 'success' : 'info'" size="small">
              {{ row.bspUserId ? '已绑定' : '未绑定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="code in row.roleCodes" :key="code" size="small" style="margin-right:4px">
              {{ roleLabel(code) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dataScope" label="数据范围" width="100" />
        <el-table-column prop="regionName" label="区划" width="110" show-overflow-tooltip />
        <el-table-column prop="departmentName" label="部门/中心" width="140" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'" size="small">
              {{ row.status === 'ACTIVE' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="160">
          <template #default="{ row }">{{ formatDateTime(row.lastLoginAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openForm(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'ACTIVE' ? 'warning' : 'success'"
              @click="handleToggle(row)"
            >{{ row.status === 'ACTIVE' ? '禁用' : '启用' }}</el-button>
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

    <el-dialog
      v-model="formVisible"
      :title="editingId ? '编辑管理员' : '新增管理员'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px">
        这里只维护本系统的账号档案与授权，不设置密码——账号首次通过统一身份认证登录时，
        会按账号名自动完成一次性安全绑定（要求账号名与统一身份平台一致，且当前未绑定过其他人）。
      </el-alert>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="需与统一身份平台账号一致" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="form.realName" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.mobile" placeholder="可选" />
        </el-form-item>
        <el-form-item label="角色" prop="roleCodes">
          <el-select v-model="form.roleCodes" multiple style="width:100%" placeholder="选择一个或多个角色">
            <el-option v-for="r in ADMIN_ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据范围" prop="dataScope">
          <el-select v-model="form.dataScope" style="width:100%">
            <el-option label="全部（市级/平台）" value="ALL" />
            <el-option label="本区县/本企服中心" value="REGION" />
            <el-option label="本部门" value="DEPARTMENT" />
            <el-option label="仅本人" value="SELF" />
          </el-select>
        </el-form-item>
        <el-form-item label="区划">
          <el-select v-model="form.regionCode" placeholder="可选" clearable style="width:100%" @change="onRegionChange">
            <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门/中心ID">
          <el-input v-model="form.departmentId" placeholder="可选，如对应服务中心ID" />
        </el-form-item>
        <el-form-item label="部门/中心名称">
          <el-input v-model="form.departmentName" placeholder="可选" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  listAdminUsers, createAdminUser, updateAdminUser, toggleAdminUserStatus,
  type AdminUserItem,
} from '@/api/adminUser'
import { getDictionary } from '@/api/common'
import { ADMIN_ROLE_OPTIONS } from '@/constants/permission'

const loading = ref(false)
const submitting = ref(false)
const list = ref<AdminUserItem[]>([])
const total = ref(0)
const pageNo = ref(1)
const pageSize = ref(20)
const formVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const regionOptions = ref<{ value: string; label: string }[]>([])

const filter = reactive({
  username: '',
  status: '' as '' | 'ACTIVE' | 'DISABLED',
  roleCode: '',
})

const form = reactive({
  username: '',
  realName: '',
  mobile: '',
  roleCodes: [] as string[],
  dataScope: 'SELF',
  regionCode: '',
  regionName: '',
  departmentId: '',
  departmentName: '',
})

const formRules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  roleCodes: [{ required: true, type: 'array', min: 1, message: '请至少选择一个角色', trigger: 'change' }],
}

function roleLabel(code: string): string {
  return ADMIN_ROLE_OPTIONS.find((r) => r.value === code)?.label.replace(/\s*\(.+\)$/, '') || code
}

function formatDateTime(value?: string | null): string {
  if (!value) return '从未登录'
  return value.replace('T', ' ').slice(0, 19)
}

async function fetchList() {
  loading.value = true
  try {
    const res = await listAdminUsers({
      username: filter.username || undefined,
      status: filter.status || undefined,
      roleCode: filter.roleCode || undefined,
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

function handleReset() {
  filter.username = ''
  filter.status = ''
  filter.roleCode = ''
  pageNo.value = 1
  fetchList()
}

function onRegionChange(regionCode: string) {
  const opt = regionOptions.value.find((r) => r.value === regionCode)
  form.regionName = opt?.label || ''
}

function openForm(row?: AdminUserItem) {
  editingId.value = row?.id ?? null
  if (row) {
    Object.assign(form, {
      username: row.username,
      realName: row.realName,
      mobile: row.mobile || '',
      roleCodes: [...row.roleCodes],
      dataScope: row.dataScope,
      regionCode: row.regionCode || '',
      regionName: row.regionName || '',
      departmentId: row.departmentId || '',
      departmentName: row.departmentName || '',
    })
  } else {
    Object.assign(form, {
      username: '', realName: '', mobile: '', roleCodes: [], dataScope: 'SELF',
      regionCode: '', regionName: '', departmentId: '', departmentName: '',
    })
  }
  formRef.value?.clearValidate()
  formVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      username: form.username,
      realName: form.realName,
      mobile: form.mobile || undefined,
      roleCodes: form.roleCodes,
      dataScope: form.dataScope,
      regionCode: form.regionCode || undefined,
      regionName: form.regionName || undefined,
      departmentId: form.departmentId || undefined,
      departmentName: form.departmentName || undefined,
    }
    if (editingId.value) {
      await updateAdminUser(editingId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createAdminUser(payload)
      ElMessage.success('新增成功')
    }
    formVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

async function handleToggle(row: AdminUserItem) {
  const status = row.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE'
  const action = status === 'ACTIVE' ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定${action}管理员「${row.realName}（${row.username}）」吗？`, '确认', { type: 'warning' })
  } catch {
    return
  }
  await toggleAdminUserStatus(row.id, status)
  ElMessage.success(status === 'ACTIVE' ? '已启用' : '已禁用')
  fetchList()
}

async function loadRegionOptions() {
  const regions = await getDictionary('REGION')
  regionOptions.value = regions.map((d) => ({ value: d.dictCode, label: d.dictLabel }))
}

onMounted(async () => {
  await loadRegionOptions()
  fetchList()
})
</script>

<style scoped>
.admin-user-manage { min-height: calc(100vh - 120px); }
.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}
.page-header h2 { margin: 0; font-size: 18px; }
.page-hint { color: #909399; font-size: 13px; }
.table-card { padding: 4px 4px 0; }
.filter-inline { margin-bottom: 12px; display: flex; flex-wrap: wrap; align-items: center; }
.filter-inline :deep(.el-form-item) { margin-bottom: 8px; }
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin: 16px 0;
}
</style>
