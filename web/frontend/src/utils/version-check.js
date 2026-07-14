/**
 * 版本号比较与兼容性校验工具
 */

/**
 * 将语义化版本号字符串解析为可比较的数字数组
 * 如 "1.2.3" -> [1, 2, 3]
 * 无法解析的部分视为 0
 */
function parseVersion(v) {
  if (!v || typeof v !== 'string') return [0]
  const parts = v.split('.').map((s) => {
    const n = parseInt(s, 10)
    return isNaN(n) ? 0 : n
  })
  return parts.length > 0 ? parts : [0]
}

/**
 * 比较两个版本号
 * @returns {number} -1 if a < b, 0 if a == b, 1 if a > b
 */
export function compareVersions(a, b) {
  const pa = parseVersion(a)
  const pb = parseVersion(b)
  const len = Math.max(pa.length, pb.length)
  for (let i = 0; i < len; i++) {
    const na = pa[i] || 0
    const nb = pb[i] || 0
    if (na < nb) return -1
    if (na > nb) return 1
  }
  return 0
}

/**
 * 版本校验结果类型
 * - ok: 完全兼容
 * - incompatible: 完全不兼容（拒绝连接）
 * - partial: 部分兼容（允许连接但部分功能不可用）
 */
export const COMPAT_RESULT = {
  OK: 'ok',
  INCOMPATIBLE: 'incompatible',
  PARTIAL: 'partial'
}

/**
 * 校验 node 版本信息与客户端的兼容性
 *
 * @param {Object} versionInfo - node /api/version 返回的数据
 *   { version, api_version, min_client_version, features }
 * @param {Object} clientConfig - 客户端版本配置
 *   { clientVersion, clientApiVersion, minNodeVersion, clientFeatures, requiredFeatures, featureRegistry }
 * @returns {Object} { result, reason, missingFeatures, unsupportedFeatures }
 *   - result: COMPAT_RESULT 之一
 *   - reason: 不兼容原因（ok 时为空字符串）
 *   - missingFeatures: node 不支持但客户端期望的功能列表（partial 时有值）
 *   - unsupportedFeatures: 客户端不支持但 node 提供的功能列表（仅参考，不影响连接）
 */
export function checkCompatibility(versionInfo, clientConfig) {
  const {
    clientApiVersion,
    minNodeVersion,
    clientFeatures,
    requiredFeatures,
    featureRegistry
  } = clientConfig

  if (!versionInfo || !versionInfo.version) {
    return {
      result: COMPAT_RESULT.INCOMPATIBLE,
      reason: '节点未返回版本信息，可能版本过低',
      missingFeatures: [],
      unsupportedFeatures: []
    }
  }

  // 1. API 协议主版本不兼容 → 拒绝连接
  const nodeApiVersion = versionInfo.api_version
  if (typeof nodeApiVersion === 'number' && nodeApiVersion !== clientApiVersion) {
    return {
      result: COMPAT_RESULT.INCOMPATIBLE,
      reason: `API 协议不兼容（节点 v${nodeApiVersion}，客户端 v${clientApiVersion}）`,
      missingFeatures: [],
      unsupportedFeatures: []
    }
  }

  // 2. node 版本过低 → 拒绝连接
  if (compareVersions(versionInfo.version, minNodeVersion) < 0) {
    return {
      result: COMPAT_RESULT.INCOMPATIBLE,
      reason: `节点版本过低（v${versionInfo.version}，需 v${minNodeVersion} 以上）`,
      missingFeatures: [],
      unsupportedFeatures: []
    }
  }

  // 3. node 要求的最低客户端版本校验
  if (versionInfo.min_client_version) {
    const clientVersion = clientConfig.clientVersion
    if (compareVersions(clientVersion, versionInfo.min_client_version) < 0) {
      return {
        result: COMPAT_RESULT.INCOMPATIBLE,
        reason: `客户端版本过低（v${clientVersion}，节点要求 v${versionInfo.min_client_version} 以上）`,
        missingFeatures: [],
        unsupportedFeatures: []
      }
    }
  }

  // 4. 功能能力对比
  const nodeFeatures = Array.isArray(versionInfo.features) ? versionInfo.features : []
  const missingFeatures = clientFeatures.filter(
    (f) => !nodeFeatures.includes(f) && featureRegistry[f]
  )
  const unsupportedFeatures = nodeFeatures.filter(
    (f) => !clientFeatures.includes(f)
  )

  // 5. 核心功能缺失 → 拒绝连接
  const missingRequired = missingFeatures.filter((f) => requiredFeatures.includes(f))
  if (missingRequired.length > 0) {
    const labels = missingRequired.map((f) => featureRegistry[f].label).join('、')
    return {
      result: COMPAT_RESULT.INCOMPATIBLE,
      reason: `核心功能缺失：${labels}，请升级 node`,
      missingFeatures,
      unsupportedFeatures
    }
  }

  // 6. 非核心功能缺失 → 部分兼容
  if (missingFeatures.length > 0) {
    return {
      result: COMPAT_RESULT.PARTIAL,
      reason: '',
      missingFeatures,
      unsupportedFeatures
    }
  }

  return {
    result: COMPAT_RESULT.OK,
    reason: '',
    missingFeatures: [],
    unsupportedFeatures
  }
}
