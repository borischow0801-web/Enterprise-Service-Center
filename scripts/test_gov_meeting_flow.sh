#!/usr/bin/env bash
# End-to-end test for Government-Enterprise Meeting (政企约见) module
set -euo pipefail

BASE="http://localhost:8000"
PASS=0; FAIL=0

# ── helpers ──────────────────────────────────────────────────────────────────
assert_eq() {
    local label="$1" expected="$2" actual="$3"
    if [ "$actual" = "$expected" ]; then
        echo "[PASS] $label"
        PASS=$((PASS+1))
    else
        echo "[FAIL] $label | expected=$expected actual=$actual"
        FAIL=$((FAIL+1))
    fi
}

jget() { echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print($2)" 2>/dev/null || echo ""; }

# ── unique identifiers ────────────────────────────────────────────────────────
TS=$(date +%s)
ENT_CODE="91371000GM${TS}"
ADMIN_CODE="admin_gov_${TS}"

# ── 1. Login ─────────────────────────────────────────────────────────────────
echo "=== 1. Login ==="
ENT_RESP=$(curl -s -X POST "$BASE/api/auth/enterprise/mock-login" \
  -H "Content-Type: application/json" \
  -d "{\"creditCode\":\"$ENT_CODE\",\"enterpriseName\":\"政企约见测试企业${TS}\",\"legalPersonName\":\"张三\",\"legalPersonIdNo\":\"370102199001011234\",\"legalPersonMobile\":\"13800138000\"}")
ENT_TOKEN=$(jget "$ENT_RESP" "d['data']['accessToken']")
assert_eq "企业登录成功" "0" "$(jget "$ENT_RESP" "d['code']")"

ADMIN_RESP=$(curl -s -X POST "$BASE/api/auth/admin/mock-login" \
  -H "Content-Type: application/json" \
  -d "{\"platformUserId\":\"$ADMIN_CODE\",\"username\":\"govadmin${TS}\",\"realName\":\"政企约见管理员\",\"departmentId\":\"dept_gov_001\",\"departmentName\":\"政企约见部门\",\"regionCode\":\"370100\",\"regionName\":\"济南市\",\"roleCodes\":[\"ADMIN\"],\"dataScope\":\"ALL\"}")
ADMIN_TOKEN=$(jget "$ADMIN_RESP" "d['data']['accessToken']")
assert_eq "管理员登录成功" "0" "$(jget "$ADMIN_RESP" "d['code']")"

# ── 2. Submit application ─────────────────────────────────────────────────────
echo ""
echo "=== 2. Submit Application ==="
SUBMIT_RESP=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"contactName\": \"李四\",
    \"contactPhone\": \"13812345678\",
    \"topicCode\": \"POLICY_CONSULT\",
    \"topicName\": \"政策咨询\",
    \"meetingLevel\": \"DEPARTMENT_LEADER\",
    \"description\": \"希望就企业税收优惠政策进行咨询，我公司已在园区注册3年。\",
    \"commitmentChecked\": 1,
    \"regionCode\": \"370100\",
    \"regionName\": \"济南市\"
  }")
assert_eq "提交申请成功" "0" "$(jget "$SUBMIT_RESP" "d['code']")"
APPLY_ID=$(jget "$SUBMIT_RESP" "d['data']['id']")
APPLY_STATUS=$(jget "$SUBMIT_RESP" "d['data']['status']")
assert_eq "申请初始状态=PENDING_AUDIT" "PENDING_AUDIT" "$APPLY_STATUS"
APPLY_NO=$(jget "$SUBMIT_RESP" "d['data']['applyNo']")
assert_eq "申请编号以GM开头" "GM" "${APPLY_NO:0:2}"

# ── 3. Submit without commitment should fail ─────────────────────────────────
echo ""
echo "=== 3. Commitment Validation ==="
NOCOMMIT_RESP=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"contactName\": \"张三\",
    \"contactPhone\": \"13800000000\",
    \"description\": \"测试\",
    \"commitmentChecked\": 0,
    \"regionCode\": \"370100\",
    \"regionName\": \"济南市\"
  }")
assert_eq "未勾选承诺应报错" "40001" "$(jget "$NOCOMMIT_RESP" "d['code']")"

# ── 4. Enterprise list ────────────────────────────────────────────────────────
echo ""
echo "=== 4. Enterprise List ==="
LIST_ENT=$(curl -s "$BASE/api/enterprise/gov-meetings?pageNo=1&pageSize=10" \
  -H "Authorization: Bearer $ENT_TOKEN")
assert_eq "企业列表获取成功" "0" "$(jget "$LIST_ENT" "d['code']")"
LIST_COUNT=$(echo "$LIST_ENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['records']))" 2>/dev/null || echo "0")
assert_eq "企业列表有记录" "1" "$LIST_COUNT"

# ── 5. Enterprise detail ──────────────────────────────────────────────────────
echo ""
echo "=== 5. Enterprise Detail ==="
DETAIL_ENT=$(curl -s "$BASE/api/enterprise/gov-meetings/$APPLY_ID" \
  -H "Authorization: Bearer $ENT_TOKEN")
assert_eq "企业详情获取成功" "0" "$(jget "$DETAIL_ENT" "d['code']")"
TRAIL_0=$(echo "$DETAIL_ENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['auditTrail']))" 2>/dev/null || echo "0")
assert_eq "详情包含auditTrail(1条)" "1" "$TRAIL_0"

# ── 6. Modify application ─────────────────────────────────────────────────────
echo ""
echo "=== 6. Modify Application ==="
MODIFY_RESP=$(curl -s -X PUT "$BASE/api/enterprise/gov-meetings/$APPLY_ID" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"contactName\": \"王五\", \"meetingLevel\": \"CITY_LEADER\"}")
assert_eq "修改申请成功" "0" "$(jget "$MODIFY_RESP" "d['code']")"

# ── 7. Admin list ─────────────────────────────────────────────────────────────
echo ""
echo "=== 7. Admin List ==="
ADMIN_LIST=$(curl -s "$BASE/api/admin/gov-meetings?pageNo=1&pageSize=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
assert_eq "管理员列表获取成功" "0" "$(jget "$ADMIN_LIST" "d['code']")"
ADMIN_TOTAL=$(echo "$ADMIN_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['total'])" 2>/dev/null || echo "-1")
assert_eq "管理员列表total>=1" "true" "$([ "$ADMIN_TOTAL" -ge 1 ] && echo true || echo false)"

# ── 8. Admin detail ───────────────────────────────────────────────────────────
echo ""
echo "=== 8. Admin Detail ==="
ADMIN_DETAIL=$(curl -s "$BASE/api/admin/gov-meetings/$APPLY_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
assert_eq "管理员详情获取成功" "0" "$(jget "$ADMIN_DETAIL" "d['code']")"

# ── 9. Admin audit - return supplement ───────────────────────────────────────
echo ""
echo "=== 9. Return Supplement ==="
RETURN_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/audit" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"auditType\": \"RETURN_SUPPLEMENT\", \"opinion\": \"申请材料不完整，请补充说明\"}")
assert_eq "退回补正成功" "0" "$(jget "$RETURN_RESP" "d['code']")"
assert_eq "状态变为NEED_SUPPLEMENT" "NEED_SUPPLEMENT" "$(jget "$RETURN_RESP" "d['data']['status']")"

# ── 10. Enterprise supplement ─────────────────────────────────────────────────
echo ""
echo "=== 10. Enterprise Supplement ==="
SUP_RESP=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings/$APPLY_ID/supplement" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"description\": \"补充说明：我公司已提交相关税务证明材料，请审核\"}")
assert_eq "补充材料成功" "0" "$(jget "$SUP_RESP" "d['code']")"
assert_eq "状态变为PENDING_AUDIT" "PENDING_AUDIT" "$(jget "$SUP_RESP" "d['data']['status']")"

# ── 11. Admin audit - accept ──────────────────────────────────────────────────
echo ""
echo "=== 11. Accept Application ==="
ACCEPT_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/audit" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"auditType\": \"ACCEPT\", \"opinion\": \"申请符合条件，予以受理\"}")
assert_eq "受理通过成功" "0" "$(jget "$ACCEPT_RESP" "d['code']")"
assert_eq "状态变为PENDING_ARRANGE" "PENDING_ARRANGE" "$(jget "$ACCEPT_RESP" "d['data']['status']")"

# ── 12. Wrong action on wrong status ─────────────────────────────────────────
echo ""
echo "=== 12. Status Guard ==="
WRONG_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/audit" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"auditType\": \"ACCEPT\"}")
assert_eq "重复受理应报错" "40901" "$(jget "$WRONG_RESP" "d['code']")"

# ── 13. Arrange ───────────────────────────────────────────────────────────────
echo ""
echo "=== 13. Arrange Meeting ==="
ARRANGE_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/arrange" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"meetingDate\": \"2026-06-15T09:00:00\",
    \"meetingPlace\": \"市政大厅第三会议室\",
    \"meetingMethod\": \"ON_SITE\",
    \"govContactName\": \"陈部长\",
    \"govContactPhone\": \"0531-88888888\",
    \"remark\": \"请准时参加\",
    \"participants\": [
      {\"participantType\": \"GOV\", \"participantName\": \"陈部长\", \"participantTitle\": \"局长\", \"sortNo\": 1},
      {\"participantType\": \"ENTERPRISE\", \"participantName\": \"王五\", \"participantTitle\": \"法人\", \"sortNo\": 1}
    ]
  }")
assert_eq "安排约见成功" "0" "$(jget "$ARRANGE_RESP" "d['code']")"
ARR_ID=$(jget "$ARRANGE_RESP" "d['data']['id']")
PART_COUNT=$(echo "$ARRANGE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['participants']))" 2>/dev/null || echo "0")
assert_eq "参与人2人" "2" "$PART_COUNT"

# Verify status changed to ARRANGED
ARR_STATUS=$(curl -s "$BASE/api/admin/gov-meetings/$APPLY_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['status'])" 2>/dev/null || echo "")
assert_eq "安排后状态为ARRANGED" "ARRANGED" "$ARR_STATUS"

# ── 14. Update arrangement ────────────────────────────────────────────────────
echo ""
echo "=== 14. Update Arrangement ==="
UPD_ARR=$(curl -s -X PUT "$BASE/api/admin/gov-meetings/$APPLY_ID/arrangements/$ARR_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"meetingPlace\": \"市政大厅第一会议室\",
    \"participants\": [
      {\"participantType\": \"GOV\", \"participantName\": \"陈部长\", \"participantTitle\": \"局长\", \"sortNo\": 1},
      {\"participantType\": \"GOV\", \"participantName\": \"李副局长\", \"participantTitle\": \"副局长\", \"sortNo\": 2},
      {\"participantType\": \"ENTERPRISE\", \"participantName\": \"王五\", \"participantTitle\": \"法人\", \"sortNo\": 1}
    ]
  }")
assert_eq "修改安排成功" "0" "$(jget "$UPD_ARR" "d['code']")"
UPD_PART_COUNT=$(echo "$UPD_ARR" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['participants']))" 2>/dev/null || echo "0")
assert_eq "更新后参与人3人" "3" "$UPD_PART_COUNT"

# ── 15. Confirm ───────────────────────────────────────────────────────────────
echo ""
echo "=== 15. Confirm Arrangement ==="
CONFIRM_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/confirm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"opinion\": \"请准时参加约见\"}")
assert_eq "确认安排成功" "0" "$(jget "$CONFIRM_RESP" "d['code']")"
assert_eq "状态变为WAIT_MEETING" "WAIT_MEETING" "$(jget "$CONFIRM_RESP" "d['data']['status']")"

# ── 16. Complete meeting ──────────────────────────────────────────────────────
echo ""
echo "=== 16. Complete Meeting ==="
COMPLETE_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/complete" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"meetingAt\": \"2026-06-15T10:30:00\", \"opinion\": \"约见顺利完成\"}")
assert_eq "约见完成成功" "0" "$(jget "$COMPLETE_RESP" "d['code']")"
assert_eq "状态变为MEETING_COMPLETED" "MEETING_COMPLETED" "$(jget "$COMPLETE_RESP" "d['data']['status']")"

# ── 17. Add record ────────────────────────────────────────────────────────────
echo ""
echo "=== 17. Add Meeting Record ==="
RECORD_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/record" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"arrangementId\": $ARR_ID,
    \"content\": \"本次约见围绕企业税收优惠政策展开讨论。\",
    \"conclusions\": \"将为企业申请相关政策扶持。\",
    \"followUpItems\": \"1. 提交材料清单 2. 一周内反馈结果\",
    \"recordTime\": \"2026-06-15T11:00:00\"
  }")
assert_eq "填写纪要成功" "0" "$(jget "$RECORD_RESP" "d['code']")"

# Verify record exists in detail
REC_DETAIL=$(curl -s "$BASE/api/admin/gov-meetings/$APPLY_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
REC_COUNT=$(echo "$REC_DETAIL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['records']))" 2>/dev/null || echo "0")
assert_eq "详情中有1条纪要" "1" "$REC_COUNT"

# ── 18. Finish (send evaluation) ─────────────────────────────────────────────
echo ""
echo "=== 18. Finish - Send Evaluation ==="
FINISH_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/finish" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sendEvaluation\": 1, \"opinion\": \"请企业对本次约见进行评价\"}")
assert_eq "触发评价成功" "0" "$(jget "$FINISH_RESP" "d['code']")"
assert_eq "状态变为PENDING_EVALUATION" "PENDING_EVALUATION" "$(jget "$FINISH_RESP" "d['data']['status']")"

# ── 19. Enterprise cannot evaluate wrong apply ────────────────────────────────
echo ""
echo "=== 19. Wrong Apply Evaluate Guard ==="
WRONG_EVAL=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings/999999/evaluate" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"satisfaction\": \"SATISFIED\", \"score\": 5}")
assert_eq "评价不存在申请应报404" "40401" "$(jget "$WRONG_EVAL" "d['code']")"

# ── 20. Enterprise evaluate ───────────────────────────────────────────────────
echo ""
echo "=== 20. Enterprise Evaluate ==="
EVAL_RESP=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings/$APPLY_ID/evaluate" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"satisfaction\": \"SATISFIED\",
    \"score\": 5,
    \"resolvedFlag\": 1,
    \"comment\": \"政府工作人员非常专业，问题得到圆满解决。\"
  }")
assert_eq "企业评价成功" "0" "$(jget "$EVAL_RESP" "d['code']")"
assert_eq "状态变为EVALUATED" "EVALUATED" "$(jget "$EVAL_RESP" "d['data']['status']")"

# ── 21. Duplicate evaluation should fail ─────────────────────────────────────
echo ""
echo "=== 21. Duplicate Evaluation Guard ==="
DUP_EVAL=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings/$APPLY_ID/evaluate" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"satisfaction\": \"SATISFIED\", \"score\": 4}")
assert_eq "重复评价应报错(状态不允许)" "40901" "$(jget "$DUP_EVAL" "d['code']")"

# ── 22. Admin finish (close) ──────────────────────────────────────────────────
echo ""
echo "=== 22. Admin Finish (Close) ==="
CLOSE_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$APPLY_ID/finish" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sendEvaluation\": 0, \"opinion\": \"办结\"}")
assert_eq "办结成功" "0" "$(jget "$CLOSE_RESP" "d['code']")"
assert_eq "最终状态为COMPLETED" "COMPLETED" "$(jget "$CLOSE_RESP" "d['data']['status']")"

# ── 23. Detail final check ────────────────────────────────────────────────────
echo ""
echo "=== 23. Final Detail Check ==="
FINAL=$(curl -s "$BASE/api/enterprise/gov-meetings/$APPLY_ID" \
  -H "Authorization: Bearer $ENT_TOKEN")
assert_eq "最终详情获取成功" "0" "$(jget "$FINAL" "d['code']")"
assert_eq "evaluation不为空" "True" "$(echo "$FINAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['evaluation'] is not None)" 2>/dev/null || echo "")"
AUDIT_COUNT=$(echo "$FINAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['auditTrail']))" 2>/dev/null || echo "0")
assert_eq "审核流水记录条数>=8" "true" "$([ "$AUDIT_COUNT" -ge 8 ] && echo true || echo false)"

# ── 24. Reject flow (new apply) ───────────────────────────────────────────────
echo ""
echo "=== 24. Reject Flow ==="
REJ_SUBMIT=$(curl -s -X POST "$BASE/api/enterprise/gov-meetings" \
  -H "Authorization: Bearer $ENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"contactName\": \"赵六\",
    \"contactPhone\": \"13700000000\",
    \"description\": \"希望约见市长讨论个人事务\",
    \"commitmentChecked\": 1,
    \"regionCode\": \"370100\",
    \"regionName\": \"济南市\"
  }")
REJ_ID=$(jget "$REJ_SUBMIT" "d['data']['id']")
assert_eq "新申请提交成功" "0" "$(jget "$REJ_SUBMIT" "d['code']")"

REJ_RESP=$(curl -s -X POST "$BASE/api/admin/gov-meetings/$REJ_ID/audit" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"auditType\": \"REJECT\", \"rejectReasonCode\": \"NON_ENTERPRISE_OPERATION\", \"rejectReasonName\": \"非企业经营事项\", \"opinion\": \"申请事项不属于企业经营范畴\"}")
assert_eq "驳回申请成功" "0" "$(jget "$REJ_RESP" "d['code']")"
assert_eq "状态为REJECTED" "REJECTED" "$(jget "$REJ_RESP" "d['data']['status']")"
assert_eq "驳回原因已记录" "NON_ENTERPRISE_OPERATION" "$(jget "$REJ_RESP" "d['data']['rejectReasonCode']")"

# ── 25. Filter by status ──────────────────────────────────────────────────────
echo ""
echo "=== 25. Filter by Status ==="
FILTER_RESP=$(curl -s "$BASE/api/admin/gov-meetings?status=REJECTED&pageNo=1&pageSize=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
assert_eq "按状态筛选成功" "0" "$(jget "$FILTER_RESP" "d['code']")"
FILTER_TOTAL=$(echo "$FILTER_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['total'])" 2>/dev/null || echo "0")
assert_eq "筛选REJECTED至少1条" "true" "$([ "$FILTER_TOTAL" -ge 1 ] && echo true || echo false)"

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "======================================"
echo "TOTAL: $((PASS+FAIL))  PASS: $PASS  FAIL: $FAIL"
echo "======================================"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
