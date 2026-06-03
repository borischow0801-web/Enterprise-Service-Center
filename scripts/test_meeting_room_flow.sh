#!/usr/bin/env bash
# ============================================================
# 共享会议室模块端到端测试脚本
# 覆盖：新增会议室 → 配置规则 → 配置材料 → 手工占用
#       → 企业提交预约 → 管理端审核 → 时间冲突 → 取消
#       → 完成 → 爽约 → 企业预约资格限制
# ============================================================

BASE="http://localhost:8001"
PASS=0
FAIL=0

GREEN="\033[0;32m"; RED="\033[0;31m"; YELLOW="\033[1;33m"; CYAN="\033[0;36m"; NC="\033[0m"

ok()   { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1 | 响应: $2"; FAIL=$((FAIL+1)); }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
sep()  { echo -e "${YELLOW}──────────────────────────────────────────${NC}"; }

post_anon() { curl -s -X POST "$BASE$1" -H "Content-Type: application/json" -d "$2"; }
post()      { curl -s -X POST "$BASE$1" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$2"; }
get()       { curl -s "$BASE$1" -H "Authorization: Bearer $TOKEN"; }
put()       { curl -s -X PUT "$BASE$1" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$2"; }
patch_req() { curl -s -X PATCH "$BASE$1" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$2"; }
del()       { curl -s -X DELETE "$BASE$1" -H "Authorization: Bearer $TOKEN"; }

jfield() { echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d$2)" 2>/dev/null; }
jcount() { echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d$2))" 2>/dev/null || echo 0; }

assert_code() {
  local code; code=$(jfield "$1" "['code']")
  [ "$code" = "$2" ] && ok "$3 (code=$code)" || fail "$3 (期望=$2, 实际=$code)" "$1"
}
assert_field() {
  local val; val=$(jfield "$1" "$2")
  [ "$val" = "$3" ] && ok "$4 ($val)" || fail "$4 (期望=$3, 实际=$val)" ""
}

# ── 预约时间（当前时间 + 3 天的工作日） ──────────────────────
# Python 计算：找 3 天后且为周一到周五的日期
read -r BOOK_DATE BOOK_WEEKDAY <<< $(python3 -c "
from datetime import datetime, timedelta
d = datetime.utcnow() + timedelta(days=3)
while d.isoweekday() >= 6:
    d += timedelta(days=1)
print(d.strftime('%Y-%m-%d'), d.isoweekday())
")
START_TIME="${BOOK_DATE} 09:00:00"
END_TIME="${BOOK_DATE} 11:00:00"
START2="${BOOK_DATE} 09:30:00"
END2="${BOOK_DATE} 10:30:00"
info "预约测试日期: $BOOK_DATE（周$BOOK_WEEKDAY）"

# ============================================================
sep; info "【准备】管理端登录"; sep
ADMIN_RESP=$(post_anon "/api/auth/admin/mock-login" '{
  "platformUserId":"room_admin_001","username":"lihua","realName":"李华",
  "departmentId":"center_001","departmentName":"企业服务中心",
  "regionCode":"371000","regionName":"威海市",
  "roleCodes":["CENTER_ADMIN"],"dataScope":"ALL"
}')
assert_code "$ADMIN_RESP" "0" "管理端登录"
ADMIN_TOKEN=$(jfield "$ADMIN_RESP" "['data']['accessToken']")

# ============================================================
sep; info "【Step 6】新增会议室"; sep
TOKEN="$ADMIN_TOKEN"
ROOM_RESP=$(post "/api/admin/meeting-rooms" '{
  "roomName":"威海市企服中心一号会议室",
  "roomType":"MEETING",
  "regionCode":"371000","regionName":"威海市",
  "serviceCenterId":1,"serviceCenterName":"威海市企业综合服务中心",
  "address":"威海市环翠区文化西路1号",
  "capacity":30,
  "facilities":["话筒音箱","投屏","电脑","白板"],
  "description":"标准会议室，适合20-30人中型会议",
  "bookingNotice":"请提前15分钟到场，使用结束后请还原桌椅"
}')
assert_code "$ROOM_RESP" "0" "新增会议室"
assert_field "$ROOM_RESP" "['data']['status']" "ENABLED" "新增后默认 ENABLED"
ROOM_ID=$(jfield "$ROOM_RESP" "['data']['id']")
info "会议室 ID: $ROOM_ID"

# ============================================================
sep; info "【Step 7】配置开放规则（周一到周五 09:00-18:00）"; sep
RULE_RESP=$(put "/api/admin/meeting-rooms/$ROOM_ID/open-rules" '{
  "rules":[
    {"weekday":1,"openFlag":1,"startTime":"09:00","endTime":"18:00"},
    {"weekday":2,"openFlag":1,"startTime":"09:00","endTime":"18:00"},
    {"weekday":3,"openFlag":1,"startTime":"09:00","endTime":"18:00"},
    {"weekday":4,"openFlag":1,"startTime":"09:00","endTime":"18:00"},
    {"weekday":5,"openFlag":1,"startTime":"09:00","endTime":"18:00"},
    {"weekday":6,"openFlag":0,"startTime":null,"endTime":null},
    {"weekday":7,"openFlag":0,"startTime":null,"endTime":null}
  ]
}')
assert_code "$RULE_RESP" "0" "配置开放规则"

# ============================================================
sep; info "【Step 8】配置盖章申请表材料规则"; sep
MATERIAL_RESP=$(post "/api/admin/meeting-rooms/material-rules" "{
  \"roomId\":$ROOM_ID,
  \"enterpriseType\":null,
  \"materialName\":\"盖章申请表\",
  \"materialCode\":\"STAMPED_APPLICATION_FORM\",
  \"requiredFlag\":1,
  \"description\":\"请下载模板，填写后加盖公章，上传扫描件\"
}")
assert_code "$MATERIAL_RESP" "0" "新增材料规则（盖章申请表）"
MATERIAL_ID=$(jfield "$MATERIAL_RESP" "['data']['id']")
assert_field "$MATERIAL_RESP" "['data']['requiredFlag']" "1" "必传标记正确"

# 查询材料规则列表
MAT_LIST=$(get "/api/admin/meeting-rooms/material-rules?roomId=$ROOM_ID")
assert_code "$MAT_LIST" "0" "材料规则列表查询"
MAT_COUNT=$(jcount "$MAT_LIST" "['data']")
[ "$MAT_COUNT" -ge 1 ] && ok "材料规则有数据 ($MAT_COUNT 条)" || fail "材料规则列表为空" ""

# 修改材料规则
UPD_MAT=$(put "/api/admin/meeting-rooms/material-rules/$MATERIAL_ID" '{"description":"最新说明：请下载模板填写盖章"}')
assert_code "$UPD_MAT" "0" "修改材料规则"

# ============================================================
sep; info "【配置特殊日期：后天配置为临时关闭】"; sep
CLOSE_DATE=$(python3 -c "from datetime import datetime,timedelta; print((datetime.utcnow()+timedelta(days=1)).strftime('%Y-%m-%d'))")
SPEC_RESP=$(post "/api/admin/meeting-rooms/special-dates" "{
  \"regionCode\":\"371000\",\"serviceCenterId\":1,
  \"specialDate\":\"$CLOSE_DATE\",
  \"dateType\":\"TEMP_CLOSE\",\"openFlag\":0,\"reason\":\"系统维护临时关闭\"
}")
assert_code "$SPEC_RESP" "0" "配置特殊关闭日期 ($CLOSE_DATE)"

# ============================================================
sep; info "【手工占用】占用当天 14:00-15:00"; sep
OCCUPY_RESP=$(post "/api/admin/meeting-rooms/occupies" "{
  \"roomId\":$ROOM_ID,
  \"occupyTitle\":\"中心内部例会\",
  \"occupyReason\":\"月度工作例会\",
  \"startTime\":\"${BOOK_DATE} 14:00:00\",
  \"endTime\":\"${BOOK_DATE} 15:00:00\"
}")
assert_code "$OCCUPY_RESP" "0" "手工占用会议室"

# 重复占用同一时段应冲突
OCCUPY2_RESP=$(post "/api/admin/meeting-rooms/occupies" "{
  \"roomId\":$ROOM_ID,
  \"occupyTitle\":\"重复占用测试\",
  \"startTime\":\"${BOOK_DATE} 14:30:00\",
  \"endTime\":\"${BOOK_DATE} 15:30:00\"
}")
OCCUPY2_CODE=$(jfield "$OCCUPY2_RESP" "['code']")
[ "$OCCUPY2_CODE" = "40902" ] && ok "重复占用被拦截 (code=40902)" || fail "重复占用未被拦截 (code=$OCCUPY2_CODE)" ""

# ============================================================
sep; info "【会议室详情与日历查询】"; sep
ROOM_DETAIL=$(get "/api/admin/meeting-rooms/$ROOM_ID")
assert_code "$ROOM_DETAIL" "0" "管理端会议室列表"

# ============================================================
sep; info "【企业端登录】"; sep
ENT_RESP=$(post_anon "/api/auth/enterprise/mock-login" '{
  "enterpriseName":"威海创新科技有限公司",
  "creditCode":"91371000ROOM000001",
  "legalPersonName":"王五","legalPersonIdNo":"370000199201010051",
  "legalPersonMobile":"13700000005"
}')
assert_code "$ENT_RESP" "0" "企业端登录"
ENT_TOKEN=$(jfield "$ENT_RESP" "['data']['accessToken']")
TOKEN="$ENT_TOKEN"

# ============================================================
sep; info "【企业端：查看会议室列表】"; sep
ENT_ROOMS=$(get "/api/enterprise/meeting-rooms?regionCode=371000")
assert_code "$ENT_ROOMS" "0" "企业端会议室列表"
ENT_ROOM_COUNT=$(jcount "$ENT_ROOMS" "['data']['records']")
[ "$ENT_ROOM_COUNT" -ge 1 ] && ok "企业端看到 $ENT_ROOM_COUNT 个会议室" || fail "企业端会议室列表为空" ""

# ============================================================
sep; info "【企业端：查询会议室详情和材料规则】"; sep
ENT_ROOM_DETAIL=$(get "/api/enterprise/meeting-rooms/$ROOM_ID")
assert_code "$ENT_ROOM_DETAIL" "0" "企业端会议室详情"
OPEN_RULES_COUNT=$(jcount "$ENT_ROOM_DETAIL" "['data']['openRules']")
[ "$OPEN_RULES_COUNT" -ge 7 ] && ok "开放规则加载正确 ($OPEN_RULES_COUNT 条)" || fail "开放规则数量异常 ($OPEN_RULES_COUNT)" ""

ENT_MAT=$(get "/api/enterprise/meeting-rooms/$ROOM_ID/material-rules")
assert_code "$ENT_MAT" "0" "企业端材料规则查询"
REQ_COUNT=$(echo "$ENT_MAT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len([r for r in d['data'] if r['requiredFlag']==1]))" 2>/dev/null || echo 0)
[ "$REQ_COUNT" -ge 1 ] && ok "必传材料 $REQ_COUNT 项（盖章申请表）" || fail "必传材料未找到" ""

# ============================================================
sep; info "【Step 9】企业提交预约（无附件应被必传材料拦截）"; sep
NO_ATT_RESP=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"年度供应商大会\",
  \"participantCount\":25,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"$START_TIME\",
  \"endTime\":\"$END_TIME\"
}")
NO_ATT_CODE=$(jfield "$NO_ATT_RESP" "['code']")
[ "$NO_ATT_CODE" = "40001" ] && ok "无附件被必传材料规则拦截 (code=40001)" || fail "必传材料未拦截 (code=$NO_ATT_CODE)" "$NO_ATT_RESP"

# 正常提交（传入虚拟 attachmentIds，DB中不存在也不影响业务流转）
BOOK_RESP=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"年度供应商大会\",
  \"participantCount\":25,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"$START_TIME\",
  \"endTime\":\"$END_TIME\",
  \"supportItems\":[\"话筒音箱\",\"投屏\"],
  \"attachmentIds\":[9999]
}")
assert_code "$BOOK_RESP" "0" "企业提交预约"
BOOKING_ID=$(jfield "$BOOK_RESP" "['data']['id']")
BOOKING_NO=$(jfield "$BOOK_RESP" "['data']['bookingNo']")
assert_field "$BOOK_RESP" "['data']['status']" "PENDING_AUDIT" "预约初始状态 PENDING_AUDIT"
info "预约 ID: $BOOKING_ID，编号: $BOOKING_NO"

# ============================================================
sep; info "【Step 11】测试时间冲突（同时段再次提交）"; sep
CONFLICT_RESP=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"冲突测试会议\",
  \"participantCount\":5,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"$START2\",
  \"endTime\":\"$END2\",
  \"attachmentIds\":[9998]
}")
# PENDING_AUDIT 状态不参与冲突检测，这个应该成功
CONFLICT_CODE=$(jfield "$CONFLICT_RESP" "['code']")
CONFLICT_BOOKING_ID=$(jfield "$CONFLICT_RESP" "['data']['id']")
info "待审核时段再次提交：code=$CONFLICT_CODE（待审核不冲突，符合预期）"

# ============================================================
sep; info "【Step 10】管理端审核通过第1条预约"; sep
TOKEN="$ADMIN_TOKEN"
APPROVE_RESP=$(post "/api/admin/meeting-bookings/$BOOKING_ID/approve" '{"auditOpinion":"材料齐全，予以审核通过"}')
assert_code "$APPROVE_RESP" "0" "管理端审核通过"
assert_field "$APPROVE_RESP" "['data']['status']" "APPROVED" "审核后状态为 APPROVED"

# ============================================================
sep; info "【Step 11续】审核通过后，同时段再提交应时间冲突"; sep
TOKEN="$ENT_TOKEN"
CONFLICT2_RESP=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"冲突测试2\",
  \"participantCount\":5,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"$START_TIME\",
  \"endTime\":\"$END_TIME\",
  \"attachmentIds\":[9997]
}")
CONFLICT2_CODE=$(jfield "$CONFLICT2_RESP" "['code']")
[ "$CONFLICT2_CODE" = "40902" ] && ok "审核通过后同时段冲突被拦截 (code=40902)" || fail "时间冲突未被拦截 (code=$CONFLICT2_CODE)" "$CONFLICT2_RESP"

# 与手工占用冲突测试
OCCUPY_CONFLICT=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"与手工占用冲突测试\",
  \"participantCount\":5,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"${BOOK_DATE} 14:00:00\",
  \"endTime\":\"${BOOK_DATE} 15:00:00\",
  \"attachmentIds\":[9996]
}")
OCC_CODE=$(jfield "$OCCUPY_CONFLICT" "['code']")
[ "$OCC_CODE" = "40902" ] && ok "手工占用冲突被拦截 (code=40902)" || fail "手工占用冲突未拦截 (code=$OCC_CODE)" ""

# ============================================================
sep; info "【Step 10续】管理端审核第2条预约（待审核与已通过时间重叠，审核时冲突）"; sep
TOKEN="$ADMIN_TOKEN"
if [ -n "$CONFLICT_BOOKING_ID" ] && [ "$CONFLICT_BOOKING_ID" != "None" ]; then
  APPROVE2_RESP=$(post "/api/admin/meeting-bookings/$CONFLICT_BOOKING_ID/approve" '{"auditOpinion":"测试冲突审核"}')
  APPROVE2_CODE=$(jfield "$APPROVE2_RESP" "['code']")
  [ "$APPROVE2_CODE" = "40902" ] && ok "审核时再次校验时间冲突 (code=40902)" || fail "审核时冲突校验失败 (code=$APPROVE2_CODE)" "$APPROVE2_RESP"
else
  info "跳过冲突审核测试（第2条预约未创建）"
fi

# ============================================================
sep; info "【Step 12】取消预约流程"; sep
# 新提交一条用于取消测试
TOKEN="$ENT_TOKEN"
CANCEL_BOOK_RESP=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"取消测试会议\",
  \"participantCount\":10,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"${BOOK_DATE} 15:00:00\",
  \"endTime\":\"${BOOK_DATE} 16:00:00\",
  \"attachmentIds\":[9995]
}")
assert_code "$CANCEL_BOOK_RESP" "0" "提交取消测试预约"
CANCEL_BOOK_ID=$(jfield "$CANCEL_BOOK_RESP" "['data']['id']")

# PENDING_AUDIT 直接取消（不限制提前时间）
CANCEL_RESP=$(post "/api/enterprise/meeting-bookings/$CANCEL_BOOK_ID/cancel" '{"cancelReason":"临时会议取消"}')
assert_code "$CANCEL_RESP" "0" "企业取消待审核预约"
assert_field "$CANCEL_RESP" "['data']['status']" "CANCELED" "取消后状态为 CANCELED"

# 已取消的不能再取消
CANCEL2_RESP=$(post "/api/enterprise/meeting-bookings/$CANCEL_BOOK_ID/cancel" '{"cancelReason":"重复取消测试"}')
CANCEL2_CODE=$(jfield "$CANCEL2_RESP" "['code']")
[ "$CANCEL2_CODE" = "40901" ] && ok "已取消的预约不能重复取消 (code=40901)" || fail "重复取消未拦截 (code=$CANCEL2_CODE)" ""

# ============================================================
sep; info "【Step 10b】管理端确认完成第1条预约"; sep
TOKEN="$ADMIN_TOKEN"
COMPLETE_RESP=$(post "/api/admin/meeting-bookings/$BOOKING_ID/complete" "{
  \"actualStartTime\":\"${BOOK_DATE} 09:00:00\",
  \"actualEndTime\":\"${BOOK_DATE} 11:00:00\",
  \"remark\":\"正常使用完成\"
}")
assert_code "$COMPLETE_RESP" "0" "确认使用完成"
assert_field "$COMPLETE_RESP" "['data']['status']" "COMPLETED" "完成后状态为 COMPLETED"

# ============================================================
sep; info "【Step 13】爽约 & 企业预约资格限制"; sep
# 每次用时间戳生成唯一信用代码，避免复用已被禁止的企业
NS_CODE="91371000NS$(date +%s)"
ENT2_RESP=$(post_anon "/api/auth/enterprise/mock-login" "{
  \"enterpriseName\":\"威海爽约测试企业\",
  \"creditCode\":\"$NS_CODE\",
  \"legalPersonName\":\"赵六\",\"legalPersonIdNo\":\"370000199301010061\",
  \"legalPersonMobile\":\"13600000006\"
}")
ENT2_TOKEN=$(jfield "$ENT2_RESP" "['data']['accessToken']")

# 第1次预约 & 爽约
BOOK_DATE2=$(python3 -c "
from datetime import datetime, timedelta
d = datetime.utcnow() + timedelta(days=4)
while d.isoweekday() >= 6:
    d += timedelta(days=1)
print(d.strftime('%Y-%m-%d'))
")
TOKEN="$ENT2_TOKEN"
NS_BOOK1=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"爽约测试第1次\",
  \"participantCount\":5,
  \"contactName\":\"赵六\",\"contactPhone\":\"13600000006\",
  \"startTime\":\"${BOOK_DATE2} 09:00:00\",
  \"endTime\":\"${BOOK_DATE2} 10:00:00\",
  \"attachmentIds\":[9990]
}")
assert_code "$NS_BOOK1" "0" "爽约企业提交第1条预约"
NS_BOOK1_ID=$(jfield "$NS_BOOK1" "['data']['id']")

TOKEN="$ADMIN_TOKEN"
post "/api/admin/meeting-bookings/$NS_BOOK1_ID/approve" '{"auditOpinion":"通过"}' > /dev/null
NS1_RESP=$(post "/api/admin/meeting-bookings/$NS_BOOK1_ID/no-show" '{"reason":"企业未按时使用，爽约第1次"}')
assert_code "$NS1_RESP" "0" "标记爽约第1次"
assert_field "$NS1_RESP" "['data']['status']" "NO_SHOW" "状态变为 NO_SHOW"

# 验证爽约次数
ENT2_DETAIL=$(curl -s "http://localhost:8001/api/admin/meeting-bookings/$NS_BOOK1_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
info "第1次爽约后预约状态: $(jfield "$ENT2_DETAIL" "['data']['status']")"

# 第2次预约 & 爽约 —— 爽约2次后应被限制
BOOK_DATE3=$(python3 -c "
from datetime import datetime, timedelta
d = datetime.utcnow() + timedelta(days=5)
while d.isoweekday() >= 6:
    d += timedelta(days=1)
print(d.strftime('%Y-%m-%d'))
")
TOKEN="$ENT2_TOKEN"
NS_BOOK2=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"爽约测试第2次\",
  \"participantCount\":5,
  \"contactName\":\"赵六\",\"contactPhone\":\"13600000006\",
  \"startTime\":\"${BOOK_DATE3} 09:00:00\",
  \"endTime\":\"${BOOK_DATE3} 10:00:00\",
  \"attachmentIds\":[9989]
}")
assert_code "$NS_BOOK2" "0" "爽约企业提交第2条预约"
NS_BOOK2_ID=$(jfield "$NS_BOOK2" "['data']['id']")

TOKEN="$ADMIN_TOKEN"
post "/api/admin/meeting-bookings/$NS_BOOK2_ID/approve" '{"auditOpinion":"通过"}' > /dev/null
NS2_RESP=$(post "/api/admin/meeting-bookings/$NS_BOOK2_ID/no-show" '{"reason":"企业再次未使用，爽约第2次"}')
assert_code "$NS2_RESP" "0" "标记爽约第2次"

# 爽约2次后，企业再提交应被限制
TOKEN="$ENT2_TOKEN"
DISABLED_RESP=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"被限制后测试\",
  \"participantCount\":5,
  \"contactName\":\"赵六\",\"contactPhone\":\"13600000006\",
  \"startTime\":\"${BOOK_DATE3} 14:00:00\",
  \"endTime\":\"${BOOK_DATE3} 16:00:00\",
  \"attachmentIds\":[9988]
}")
DISABLED_CODE=$(jfield "$DISABLED_RESP" "['code']")
[ "$DISABLED_CODE" = "40903" ] && ok "爽约2次后企业被限制，预约被拦截 (code=40903)" || fail "企业限制未生效 (code=$DISABLED_CODE)" "$DISABLED_RESP"

# ============================================================
sep; info "【其他功能验证】"; sep
# 退回材料补充
TOKEN="$ENT_TOKEN"
RS_BOOK=$(post "/api/enterprise/meeting-bookings" "{
  \"roomId\":$ROOM_ID,
  \"meetingSubject\":\"材料补充测试\",
  \"participantCount\":8,
  \"contactName\":\"王五\",\"contactPhone\":\"13700000005\",
  \"startTime\":\"${BOOK_DATE3} 09:00:00\",
  \"endTime\":\"${BOOK_DATE3} 11:00:00\",
  \"attachmentIds\":[9987]
}")
assert_code "$RS_BOOK" "0" "提交材料补充测试预约"
RS_ID=$(jfield "$RS_BOOK" "['data']['id']")

TOKEN="$ADMIN_TOKEN"
RS_RESP=$(post "/api/admin/meeting-bookings/$RS_ID/return-supplement" '{"auditOpinion":"请补充盖章申请表原件"}')
assert_code "$RS_RESP" "0" "退回补充材料"
assert_field "$RS_RESP" "['data']['status']" "NEED_SUPPLEMENT" "状态变为 NEED_SUPPLEMENT"

# 驳回
REJECT_BOOK_RESP=$(post "/api/admin/meeting-bookings/$RS_ID/reject" '{"auditOpinion":"材料真实性存疑，予以驳回"}')
assert_code "$REJECT_BOOK_RESP" "0" "驳回预约（从NEED_SUPPLEMENT驳回）"
assert_field "$REJECT_BOOK_RESP" "['data']['status']" "REJECTED" "驳回后状态为 REJECTED"

# 台账查询
LEDGER=$(get "/api/admin/meeting-bookings/ledger?regionCode=371000")
assert_code "$LEDGER" "0" "台账查询"
LEDGER_TOTAL=$(jfield "$LEDGER" "['data']['total']")
[ "$LEDGER_TOTAL" -ge 1 ] && ok "台账有数据 (total=$LEDGER_TOTAL)" || fail "台账为空" ""

# 导出
EXPORT=$(get "/api/admin/meeting-bookings/export?regionCode=371000")
assert_code "$EXPORT" "0" "台账导出接口"

# 启用停用测试
DISABLE_RESP=$(patch_req "/api/admin/meeting-rooms/$ROOM_ID/status" '{"status":"DISABLED"}')
assert_code "$DISABLE_RESP" "0" "停用会议室"
assert_field "$DISABLE_RESP" "['data']['status']" "DISABLED" "停用后状态为 DISABLED"

ENABLE_RESP=$(patch_req "/api/admin/meeting-rooms/$ROOM_ID/status" '{"status":"ENABLED"}')
assert_code "$ENABLE_RESP" "0" "重新启用会议室"
assert_field "$ENABLE_RESP" "['data']['status']" "ENABLED" "启用后状态为 ENABLED"

# ============================================================
sep
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        共享会议室测试完成 — 汇总结果       ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  通过 (PASS): $(printf '%2d' $PASS)                          ║${NC}"
if [ "$FAIL" -gt 0 ]; then
echo -e "${RED}║  失败 (FAIL): $(printf '%2d' $FAIL)                          ║${NC}"
else
echo -e "${GREEN}║  失败 (FAIL):  0                          ║${NC}"
fi
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
