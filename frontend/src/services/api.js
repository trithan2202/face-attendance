const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

const request = async (path, options = {}) => {
  const headers = new Headers(options.headers || {});
  const isForm = options.body instanceof FormData;
  if (options.body && !isForm) headers.set('Content-Type', 'application/json');
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      credentials: 'include',
    });
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new ApiError('Yêu cầu đã bị hủy', 0);
    }
    throw new ApiError(
      'Không thể kết nối đến backend. Hãy kiểm tra Docker và thử lại.',
      0,
    );
  }
  if (!response.ok) {
    let payload = null;
    try { payload = await response.json(); } catch { /* response has no JSON */ }
    throw new ApiError(payload?.message || `Yêu cầu thất bại (${response.status})`, response.status, payload?.details);
  }
  if (response.status === 204) return null;
  const type = response.headers.get('content-type') || '';
  return type.includes('application/json') ? response.json() : response.blob();
};

const timePart = (value) => value ? value.slice(11, 16) : '';
const statusLabel = (value) => ({
  ACTIVE: 'Active', INACTIVE: 'Inactive', PENDING_ENROLLMENT: 'Pending enrollment',
  PRESENT: 'Present', MISSING_CHECK_IN: 'Missing check-in',
  MISSING_CHECK_OUT: 'Missing check-out', ABSENT: 'Absent',
}[value] || value);
const statusValue = (value) => ({
  Active: 'ACTIVE', Inactive: 'INACTIVE', 'Pending enrollment': 'PENDING_ENROLLMENT',
  Present: 'PRESENT', 'Missing check-in': 'MISSING_CHECK_IN',
  'Missing check-out': 'MISSING_CHECK_OUT', Absent: 'ABSENT',
}[value] || value);

const mapShift = (shift) => ({
  id: shift.id,
  code: shift.code,
  name: shift.name,
  startTime: shift.start_time.slice(0, 5),
  endTime: shift.end_time.slice(0, 5),
  gracePeriod: shift.late_grace_minutes,
  earlyGracePeriod: shift.early_leave_grace_minutes,
  overnight: shift.cross_day,
});
const shiftPayload = (data) => ({
  code: data.code,
  name: data.name,
  start_time: data.startTime,
  end_time: data.endTime,
  late_grace_minutes: Number(data.gracePeriod),
  early_leave_grace_minutes: Number(data.earlyGracePeriod ?? data.gracePeriod),
  cross_day: Boolean(data.overnight),
});
const mapEmployee = (employee, shifts = []) => ({
  id: employee.id,
  code: employee.employee_code,
  name: employee.full_name,
  email: employee.email || '',
  phone: employee.phone || '',
  department: employee.department || '',
  shiftId: employee.shift_id,
  shift: shifts.find((item) => item.id === employee.shift_id)?.name || `#${employee.shift_id}`,
  status: statusLabel(employee.status),
  enrollmentStatus: employee.enrollment_status,
  sampleCount: employee.sample_count,
});
const employeePayload = (data) => ({
  employee_code: data.code,
  full_name: data.name,
  email: data.email || null,
  phone: data.phone || null,
  department: data.department || null,
  shift_id: Number(data.shiftId || data.shift),
});
const mapAttendance = (record) => ({
  id: record.id,
  employeeId: record.employee_id,
  employeeCode: record.employee_code,
  employeeName: record.full_name,
  department: record.department || '',
  shift: record.shift_code,
  date: record.work_date,
  checkInTime: timePart(record.first_check_in),
  checkOutTime: timePart(record.last_check_out),
  status: statusLabel(record.status),
  rawStatus: record.status,
  isLate: record.is_late,
  workedMinutes: record.worked_minutes,
});

export const api = {
  auth: {
    login: (username, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
    logout: () => request('/auth/logout', { method: 'POST' }),
    me: () => request('/auth/me'),
  },
  system: {
    health: () => request('/health'),
    workerStatus: () => request('/worker/status'),
  },
  shifts: {
    list: async () => (await request('/admin/shifts')).map(mapShift),
    create: (data) => request('/admin/shifts', { method: 'POST', body: JSON.stringify(shiftPayload(data)) }),
    update: (id, data) => request(`/admin/shifts/${id}`, { method: 'PUT', body: JSON.stringify(shiftPayload(data)) }),
    delete: (id) => request(`/admin/shifts/${id}`, { method: 'DELETE' }),
  },
  employees: {
    list: async () => {
      const [employees, shifts] = await Promise.all([request('/admin/employees'), api.shifts.list()]);
      return employees.map((employee) => mapEmployee(employee, shifts));
    },
    create: (data) => request('/admin/employees', { method: 'POST', body: JSON.stringify(employeePayload(data)) }),
    update: (id, data) => request(`/admin/employees/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ ...employeePayload(data), status: statusValue(data.status) }),
    }),
    delete: (id) => request(`/admin/employees/${id}`, { method: 'DELETE' }),
    startEnrollment: (id) => request(`/admin/employees/${id}/enrollment`, { method: 'POST' }),
    enrollmentStatus: (id) => request(`/admin/enrollment/${id}`),
    submitEnrollmentFrame: (id, blob) => {
      const form = new FormData(); form.append('frame', blob, 'frame.jpg');
      return request(`/admin/enrollment/${id}/frame`, { method: 'POST', body: form });
    },
    cancelEnrollment: (id) => request(`/admin/enrollment/${id}`, { method: 'DELETE' }),
  },
  attendance: {
    list: async (filters = {}) => {
      const params = new URLSearchParams();
      if (filters.date) { params.set('date_from', filters.date); params.set('date_to', filters.date); }
      if (filters.status && filters.status !== 'All') params.set('status', statusValue(filters.status));
      if (filters.employeeId) params.set('employee_id', filters.employeeId);
      if (filters.department) params.set('department', filters.department);
      const suffix = params.size ? `?${params}` : '';
      return (await request(`/admin/attendance${suffix}`)).map(mapAttendance);
    },
    update: (record, data, reason) => {
      const combine = (value) => value ? `${record.date}T${value}:00` : null;
      return request(`/admin/attendance/${record.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          first_check_in: combine(data.checkInTime),
          last_check_out: combine(data.checkOutTime),
          status: statusValue(data.status),
          reason,
        }),
      });
    },
    getAudit: async (id) => (await request(`/admin/attendance/${id}/adjustments`)).map((item) => ({
      id: item.id, user: item.admin_username, timestamp: item.created_at,
      reason: item.reason, oldValue: item.before_data, newValue: item.after_data,
    })),
    exportCsv: (filters = {}) => {
      const params = new URLSearchParams();
      if (filters.date) { params.set('date_from', filters.date); params.set('date_to', filters.date); }
      if (filters.status && filters.status !== 'All') params.set('status', statusValue(filters.status));
      return request(`/admin/attendance/export.csv?${params}`);
    },
  },
  kiosk: {
    startLiveness: () => request('/kiosk/liveness', { method: 'POST' }),
    submitLivenessFrame: (id, blob) => {
      const form = new FormData(); form.append('frame', blob, 'frame.jpg');
      return request(`/kiosk/liveness/${id}/frame`, { method: 'POST', body: form });
    },
    cancelLiveness: (id) => request(`/kiosk/liveness/${id}`, { method: 'DELETE' }),
    startRecognition: (livenessId) => request('/kiosk/recognition', {
      method: 'POST', body: JSON.stringify({ liveness_session_id: livenessId }),
    }),
    submitRecognitionFrame: (id, blob) => {
      const form = new FormData(); form.append('frame', blob, 'frame.jpg');
      return request(`/kiosk/recognition/${id}/frame`, { method: 'POST', body: form });
    },
  },
};
