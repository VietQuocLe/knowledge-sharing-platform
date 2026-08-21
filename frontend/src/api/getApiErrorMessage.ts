import axios from 'axios'

const errorTranslations: Record<string, string> = {
  'Email already registered': 'Email đã tồn tại.',
  'Incorrect email or password': 'Email hoặc mật khẩu không đúng.',
  'Inactive user': 'Tài khoản chưa được kích hoạt.',
  'Could not validate credentials': 'Không thể xác thực thông tin đăng nhập.',
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) {
    return fallback
  }

  const detail = error.response?.data?.detail
  if (typeof detail === 'string') {
    return errorTranslations[detail] ?? detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          const msgStr = String(item.msg)
          return errorTranslations[msgStr] ?? msgStr
        }
        const itemStr = String(item)
        return errorTranslations[itemStr] ?? itemStr
      })
      .join(', ')
  }

  return fallback
}
