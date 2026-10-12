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
  MISSING_CHECK_OUT: 'Missing check-out', ABSENT: 'Absent', ON_LEAVE: 'On leave',
  PENDING: 'Pending', APPROVED: 'Approved', REJECTED: 'Rejected',
}[value] || value);
const statusValue = (value) => ({
  Active: 'ACTIVE', Inactive: 'INACTIVE', 'Pending enrollment': 'PENDING_ENROLLMENT',
  Present: 'PRESENT', 'Missing check-in': 'MISSING_CHECK_IN',
  'Missing check-out': 'MISSING_CHECK_OUT', Absent: 'ABSENT', 'On leave': 'ON_LEAVE',
  Pending: 'PENDING', Approved: 'APPROVED', Rejected: 'REJECTED',
}[value] || value);
const leaveTypeLabel = (value) => ({
  ANNUAL: 'Nghỉ phép năm', SICK: 'Nghỉ ốm',
  UNPAID: 'Nghỉ không lương', OTHER: 'Khác',
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
const mapDepartment = (department) => ({
  id: department.id,
  code: department.code,
  name: department.name,
  managerName: department.manager_name || '',
  employeeCount: department.employee_count,
});
const departmentPayload = (data) => ({
  code: data.code,
  name: data.name,
  manager_name: data.managerName || null,
});
const mapEmployee = (employee, shifts = []) => ({
  id: employee.id,
  code: employee.employee_code,
  name: employee.full_name,
  email: employee.email || '',
  phone: employee.phone || '',
  nationalId: employee.national_id || '',
  departmentId: employee.department_id,
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
  national_id: data.nationalId || null,
  department_id: data.departmentId ? Number(data.departmentId) : null,
  shift_id: Number(data.shiftId || data.shift),
});
const mapLeave = (leave) => ({
  id: leave.id,
  employeeId: leave.employee_id,
  employeeCode: leave.employee_code,
  employeeName: leave.full_name,
  leaveType: leave.leave_type,
  leaveTypeLabel: leaveTypeLabel(leave.leave_type),
  startDate: leave.start_date,
  endDate: leave.end_date,
  totalDays: leave.total_days,
  reason: leave.reason,
  status: statusLabel(leave.status),
  rawStatus: leave.status,
  createdBy: leave.created_by,
  decidedAt: leave.decided_at,
  decisionNote: leave.decision_note,
  emailStatus: leave.email_status,
  emailSentAt: leave.email_sent_at,
  emailError: leave.email_error,
});
const leavePayload = (data) => ({
  employee_id: Number(data.employeeId),
  leave_type: data.leaveType,
  start_date: data.startDate,
  end_date: data.endDate,
  reason: data.reason,
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
  overtimeMinutes: record.overtime_minutes,
  overtimeStatus: statusLabel(record.overtime_status),
  rawOvertimeStatus: record.overtime_status,
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
  departments: {
    list: async () => (await request('/admin/departments')).map(mapDepartment),
    create: (data) => request('/admin/departments', { method: 'POST', body: JSON.stringify(departmentPayload(data)) }),
    update: (id, data) => request(`/admin/departments/${id}`, { method: 'PUT', body: JSON.stringify(departmentPayload(data)) }),
    delete: (id) => request(`/admin/departments/${id}`, { method: 'DELETE' }),
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
      if (filters.departmentId) params.set('department_id', filters.departmentId);
      const suffix = params.size ? `?${params}` : '';
      return (await request(`/admin/attendance${suffix}`)).map(mapAttendance);
    },
    lateTrend: async ({ days = 30, months = 6 } = {}) => {
      const data = await request(`/admin/attendance/late-trend?days=${days}&months=${months}`);
      return {
        daily: data.daily.map((item) => ({
          date: item.work_date,
          minutes: item.late_minutes,
          count: item.late_count,
        })),
        monthly: data.monthly.map((item) => ({
          year: item.year,
          month: item.month,
          minutes: item.late_minutes,
          count: item.late_count,
        })),
        comparison: {
          currentMinutes: data.comparison.current_minutes,
          previousMinutes: data.comparison.previous_minutes,
          changePercent: data.comparison.change_percent,
          days: data.comparison.days,
        },
      };
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
    getDetail: async (id) => {
      const data = await request(`/admin/attendance/${id}`);
      return {
        daily: mapAttendance(data.daily),
        events: data.events.map((event) => ({
          id: event.id,
          type: event.event_type === 'CHECK_OUT' ? 'Check-out' : 'Check-in',
          time: timePart(event.recognized_at),
          similarity: event.similarity,
        })),
        segments: data.segments.map((segment, index) => ({
          index: index + 1,
          checkIn: timePart(segment.check_in),
          checkOut: segment.check_out ? timePart(segment.check_out) : null,
          minutes: segment.minutes,
        })),
      };
    },
    decideOvertime: (id, status, reason) => request(`/admin/attendance/${id}/overtime`, {
      method: 'PATCH',
      body: JSON.stringify({ status, reason }),
    }),
    getAudit: async (id) => (await request(`/admin/attendance/${id}/adjustments`)).map((item) => ({
      id: item.id, user: item.admin_username, timestamp: item.created_at,
      reason: item.reason, oldValue: item.before_data, newValue: item.after_data,
    })),
    exportExcel: (filters = {}) => {
      const params = new URLSearchParams();
      if (filters.date) { params.set('date_from', filters.date); params.set('date_to', filters.date); }
      if (filters.status && filters.status !== 'All') params.set('status', statusValue(filters.status));
      if (filters.departmentId) params.set('department_id', filters.departmentId);
      return request(`/admin/attendance/export.xlsx?${params}`);
    },
    exportMonthlyExcel: ({ month, employeeId, departmentId } = {}) => {
      const params = new URLSearchParams();
      const [yearValue, monthValue] = (month || '').split('-');
      params.set('year', yearValue);
      params.set('month', monthValue);
      if (employeeId) params.set('employee_id', employeeId);
      if (departmentId) params.set('department_id', departmentId);
      return request(`/admin/attendance/export-monthly.xlsx?${params}`);
    },
  },
  public: {
    lookupAttendance: async ({ employeeCode, nationalId, month }) => {
      const [year, monthValue] = (month || '').split('-');
      const data = await request('/public/attendance-lookup', {
        method: 'POST',
        body: JSON.stringify({
          employee_code: employeeCode.trim(),
          national_id: nationalId.trim(),
          year: Number(year),
          month: Number(monthValue),
        }),
      });
      return {
        employeeCode: data.employee_code,
        fullName: data.full_name,
        department: data.department || '',
        shiftCode: data.shift_code || '',
        month: `${String(data.month).padStart(2, '0')}/${data.year}`,
        summary: {
          presentDays: data.summary.present_days,
          leaveDays: data.summary.leave_days,
          lateDays: data.summary.late_days,
          totalWorkedMinutes: data.summary.total_worked_minutes,
          approvedOvertimeMinutes: data.summary.approved_overtime_minutes,
        },
        days: data.days.map((day) => ({
          date: day.work_date,
          checkIn: timePart(day.check_in),
          checkOut: timePart(day.check_out),
          workedMinutes: day.worked_minutes,
          lateMinutes: day.late_minutes,
          overtimeMinutes: day.overtime_minutes,
          status: statusLabel(day.status),
        })),
      };
    },
  },
  settings: {
    list: async () => (await request('/admin/settings')).map((item) => ({
      key: item.key,
      value: item.value,
      valueType: item.value_type,
      group: item.group,
      label: item.label,
      description: item.description,
      minimum: item.minimum,
      maximum: item.maximum,
      updatedAt: item.updated_at,
    })),
    update: (key, value) => request(`/admin/settings/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value: String(value) }),
    }),
  },
  leave: {
    list: async (filters = {}) => {
      const params = new URLSearchParams();
      if (filters.status && filters.status !== 'All') params.set('status', statusValue(filters.status));
      if (filters.employeeId) params.set('employee_id', filters.employeeId);
      if (filters.dateFrom) params.set('date_from', filters.dateFrom);
      if (filters.dateTo) params.set('date_to', filters.dateTo);
      const suffix = params.size ? `?${params}` : '';
      return (await request(`/admin/leave-requests${suffix}`)).map(mapLeave);
    },
    create: (data) => request('/admin/leave-requests', {
      method: 'POST',
      body: JSON.stringify(leavePayload(data)),
    }),
    decide: (id, status, note) => request(`/admin/leave-requests/${id}/decision`, {
      method: 'PATCH',
      body: JSON.stringify({ status, note: note || null }),
    }),
    delete: (id) => request(`/admin/leave-requests/${id}`, { method: 'DELETE' }),
    resendEmail: async (id) => mapLeave(
      await request(`/admin/leave-requests/${id}/email`, { method: 'POST' }),
    ),
  },
  kiosk: {
    startLiveness: () => request('/kiosk/liveness', { method: 'POST' }),
    submitLivenessFrame: (id, blob) => {
      const form = new FormData(); form.append('frame', blob, 'frame.jpg');
      return request(`/kiosk/liveness/${id}/frame`, { method: 'POST', body: form });
    },
    cancelLiveness: (id) => request(`/kiosk/liveness/${id}`, { method: 'DELETE' }),
    startRecognition: () => request('/kiosk/recognition', { method: 'POST' }),
    submitRecognitionFrame: (id, blob) => {
      const form = new FormData(); form.append('frame', blob, 'frame.jpg');
      return request(`/kiosk/recognition/${id}/frame`, { method: 'POST', body: form });
    },
  },
};
