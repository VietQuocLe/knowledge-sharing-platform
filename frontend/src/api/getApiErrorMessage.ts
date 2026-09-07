import axios from 'axios'

const errorTranslations: Record<string, string> = {
  'Email already registered': 'Email đã tồn tại.',
  'Incorrect email or password': 'Email hoặc mật khẩu không đúng.',
  'Inactive user': 'Tài khoản chưa được kích hoạt.',
  'Could not validate credentials': 'Không thể xác thực thông tin đăng nhập.',
  // Ràng buộc xóa taxonomy
  'Cannot delete department with associated majors/subjects':
    'Không thể xóa Khoa vì vẫn còn Ngành trực thuộc. Vui lòng xóa hoặc chuyển các Ngành này trước.',
  'Cannot delete major with associated subjects':
    'Không thể xóa Ngành vì vẫn còn Môn học trực thuộc. Vui lòng xóa hoặc chuyển các Môn học này trước.',
  'Cannot delete subject with associated documents':
    'Không thể xóa Môn học vì vẫn còn Tài liệu trực thuộc. Vui lòng xóa các Tài liệu này trước.',
  // CRUD taxonomy khác
  'Department not found': 'Không tìm thấy thông tin khoa.',
  'Department already exists': 'Khoa này đã tồn tại trong hệ thống.',
  'Major not found': 'Không tìm thấy thông tin ngành.',
  'Major already exists': 'Ngành này (tên hoặc mã) đã tồn tại trong hệ thống.',
  'Subject not found': 'Không tìm thấy thông tin môn học.',
  'Subject already exists': 'Môn học này (tên hoặc mã) đã tồn tại trong hệ thống.',
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
