import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ArrowLeftRight, Check, Download, Edit2, History, Timer, X } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Table from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Modal from '../../components/ui/Modal';
import Textarea from '../../components/ui/Textarea';
import Skeleton from '../../components/ui/Skeleton';
import { statusLabelVi } from '../../utils/statusLabels';
import { formatDuration } from '../../utils/duration';

const updateSchema = z.object({
  checkInTime: z.string().optional(),
  checkOutTime: z.string().optional(),
  status: z.string().min(1, 'Vui lòng chọn trạng thái'),
  reason: z.string().min(1, 'Vui lòng nhập lý do'),
});

const Attendance = () => {
  const [records, setRecords] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  const [filterDate, setFilterDate] = useState(new Date().toISOString().split('T')[0]);
  const [reportMonth, setReportMonth] = useState(new Date().toISOString().slice(0, 7));
  const [filterStatus, setFilterStatus] = useState('All');
  const [filterDept, setFilterDept] = useState('');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const [punchDetail, setPunchDetail] = useState(null);
  const [punchLoading, setPunchLoading] = useState(false);

  const [overtimeRecord, setOvertimeRecord] = useState(null);
  const [overtimeReason, setOvertimeReason] = useState('');
  const [overtimeBusy, setOvertimeBusy] = useState(false);

  const { addToast } = useToast();

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(updateSchema)
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await mockApi.attendance.list({
        date: filterDate,
        status: filterStatus,
        departmentId: filterDept || undefined,
      });
      setRecords(data);
    } catch (err) {
      addToast('Không thể tải dữ liệu chấm công', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterDate, filterStatus, filterDept]);

  useEffect(() => {
    mockApi.departments.list()
      .then(setDepartments)
      .catch(() => addToast('Không thể tải danh sách phòng ban', 'error'));
  }, []);

  const handleOpenEdit = (record) => {
    setEditingRecord(record);
    setValue('checkInTime', record.checkInTime || '');
    setValue('checkOutTime', record.checkOutTime || '');
    setValue('status', record.status);
    setValue('reason', '');
    setIsModalOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      await mockApi.attendance.update(editingRecord, {
          checkInTime: data.checkInTime || null,
          checkOutTime: data.checkOutTime || null,
          status: data.status
        }, data.reason);
      addToast('Cập nhật bản ghi thành công', 'success');
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Thao tác thất bại', 'error');
    }
  };

  const handleOpenAudit = async (id) => {
    setIsAuditModalOpen(true);
    setAuditLoading(true);
    try {
      const logs = await mockApi.attendance.getAudit(id);
      setAuditLogs(logs);
    } catch (err) {
      addToast('Không thể tải lịch sử chỉnh sửa', 'error');
    } finally {
      setAuditLoading(false);
    }
  };

  const handleOpenPunches = async (record) => {
    setPunchDetail({ record, events: [], segments: [] });
    setPunchLoading(true);
    try {
      const detail = await mockApi.attendance.getDetail(record.id);
      setPunchDetail({ record, events: detail.events, segments: detail.segments });
    } catch (err) {
      addToast('Không thể tải lịch sử ra/vào', 'error');
      setPunchDetail(null);
    } finally {
      setPunchLoading(false);
    }
  };

  const handleDecideOvertime = async (status) => {
    if (overtimeReason.trim().length < 3) {
      addToast('Vui lòng nhập lý do (ít nhất 3 ký tự)', 'error');
      return;
    }
    setOvertimeBusy(true);
    try {
      await mockApi.attendance.decideOvertime(overtimeRecord.id, status, overtimeReason.trim());
      addToast(status === 'APPROVED' ? 'Đã duyệt tăng ca' : 'Đã từ chối tăng ca', 'success');
      setOvertimeRecord(null);
      setOvertimeReason('');
      loadData();
    } catch (err) {
      addToast(err.message || 'Thao tác thất bại', 'error');
    } finally {
      setOvertimeBusy(false);
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const handleDailyExport = async () => {
    try {
      const blob = await mockApi.attendance.exportExcel({
        date: filterDate,
        status: filterStatus,
        departmentId: filterDept || undefined,
      });
      downloadBlob(blob, `attendance_${filterDate}.xlsx`);
    } catch (err) {
      addToast('Xuất Excel theo ngày thất bại', 'error');
    }
  };

  const handleMonthlyExport = async () => {
    if (!reportMonth) {
      addToast('Vui lòng chọn tháng cần xuất báo cáo', 'error');
      return;
    }
    try {
      const blob = await mockApi.attendance.exportMonthlyExcel({
        month: reportMonth,
        departmentId: filterDept || undefined,
      });
      downloadBlob(blob, `attendance_monthly_${reportMonth}.xlsx`);
    } catch (err) {
      addToast('Xuất báo cáo tháng thất bại', 'error');
    }
  };

  const columns = [
    { header: 'Nhân viên', cell: (row) => (
        <div>
            <div className="font-medium text-neutral-900">{row.employeeName}</div>
            <div className="text-xs text-neutral-500">{row.employeeCode}</div>
        </div>
    )},
    { header: 'Phòng ban', accessorKey: 'department' },
    { header: 'Ca làm', accessorKey: 'shift' },
    { header: 'Check-in', accessorKey: 'checkInTime' },
    { header: 'Check-out', accessorKey: 'checkOutTime' },
    { header: 'Trạng thái', cell: (row) => <Badge status={row.status}>{statusLabelVi(row.status)}</Badge> },
    { header: 'Tăng ca', cell: (row) => (
      row.overtimeMinutes > 0 ? (
        <div className="flex flex-col gap-1 items-start">
          <span className="text-sm font-medium text-neutral-900">{formatDuration(row.overtimeMinutes)}</span>
          <Badge status={row.overtimeStatus}>{statusLabelVi(row.overtimeStatus)}</Badge>
        </div>
      ) : <span className="text-neutral-400">—</span>
    )},
    { header: 'Thao tác', cell: (row) => (
      <div className="flex gap-2">
        <button onClick={() => handleOpenEdit(row)} className="p-1.5 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Sửa bản ghi">
          <Edit2 className="w-4 h-4" />
        </button>
        {row.overtimeMinutes > 0 && row.rawOvertimeStatus === 'PENDING' && (
          <button onClick={() => { setOvertimeRecord(row); setOvertimeReason(''); }} className="p-1.5 text-neutral-500 hover:text-success-700 hover:bg-success-50 rounded" title="Duyệt tăng ca">
            <Timer className="w-4 h-4" />
          </button>
        )}
        <button onClick={() => handleOpenPunches(row)} className="p-1.5 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Lịch sử ra/vào">
          <ArrowLeftRight className="w-4 h-4" />
        </button>
        <button onClick={() => handleOpenAudit(row.id)} className="p-1.5 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 rounded" title="Xem lịch sử chỉnh sửa">
          <History className="w-4 h-4" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-neutral-900">Chấm công</h1>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleDailyExport} variant="secondary" className="gap-2">
            <Download className="w-4 h-4" /> Excel theo ngày
          </Button>
          <Button onClick={handleMonthlyExport} variant="secondary" className="gap-2">
            <Download className="w-4 h-4" /> Báo cáo tháng
          </Button>
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm flex flex-col sm:flex-row gap-4 items-end">
        <Input
          label="Ngày"
          type="date"
          value={filterDate}
          onChange={(e) => setFilterDate(e.target.value)}
          className="max-w-[200px]"
        />
        <Select
          label="Trạng thái"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          options={[
            { value: 'All', label: 'Tất cả trạng thái' },
            { value: 'Present', label: 'Có mặt' },
            { value: 'Missing check-in', label: 'Thiếu check-in' },
            { value: 'Missing check-out', label: 'Thiếu check-out' },
            { value: 'Absent', label: 'Vắng mặt' },
            { value: 'On leave', label: 'Nghỉ phép' },
          ]}
          className="max-w-[200px]"
        />
        <Select
          label="Phòng ban"
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
          options={[
            { value: '', label: 'Tất cả phòng ban' },
            ...departments.map(item => ({ value: item.id, label: item.name })),
          ]}
          className="max-w-[200px]"
        />
        <Input
          label="Tháng báo cáo"
          type="month"
          value={reportMonth}
          onChange={(e) => setReportMonth(e.target.value)}
          className="max-w-[200px]"
        />
      </div>

      <Table columns={columns} data={records} isLoading={loading} emptyMessage="Không có dữ liệu chấm công cho ngày này." />

      {/* Modal sửa */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Sửa bản ghi chấm công">
        {editingRecord && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
            <div className="bg-neutral-50 p-3 rounded-md mb-4 border border-neutral-200">
              <p className="text-sm font-medium">Nhân viên: {editingRecord.employeeName}</p>
              <p className="text-sm text-neutral-500">Ngày: {editingRecord.date}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input label="Giờ Check-in" type="time" {...register('checkInTime')} error={errors.checkInTime?.message} />
              <Input label="Giờ Check-out" type="time" {...register('checkOutTime')} error={errors.checkOutTime?.message} />
            </div>

            <Select
              label="Trạng thái"
              {...register('status')}
              error={errors.status?.message}
              options={[
                { value: 'Present', label: 'Có mặt' },
                { value: 'Absent', label: 'Vắng mặt' },
                { value: 'Missing check-in', label: 'Thiếu check-in' },
                { value: 'Missing check-out', label: 'Thiếu check-out' },
                { value: 'On leave', label: 'Nghỉ phép' },
              ]}
            />

            <Textarea
              label="Lý do chỉnh sửa"
              required
              placeholder="Nhập lý do cho thay đổi thủ công này"
              error={errors.reason?.message}
              {...register('reason')}
            />

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
              <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Hủy</Button>
              <Button type="submit" isLoading={isSubmitting}>Lưu thay đổi</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Modal lịch sử ra/vào */}
      <Modal
        isOpen={!!punchDetail}
        onClose={() => setPunchDetail(null)}
        title="Lịch sử ra/vào trong ngày"
        panelClassName="max-w-[560px]"
      >
        {punchDetail && (
          <div className="space-y-4 mt-4">
            <div className="bg-neutral-50 p-3 rounded-md border border-neutral-200">
              <p className="text-sm font-medium">{punchDetail.record.employeeName} ({punchDetail.record.employeeCode})</p>
              <p className="text-sm text-neutral-500">Ngày: {punchDetail.record.date}</p>
            </div>

            {punchLoading ? (
              <div className="space-y-3">
                {[1, 2].map(i => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : punchDetail.events.length === 0 ? (
              <p className="text-neutral-500 text-sm text-center py-4">Chưa có lượt quét nào trong ngày này.</p>
            ) : (
              <>
                <div>
                  <h4 className="text-sm font-semibold text-neutral-700 mb-2">Các lượt quét ({punchDetail.events.length})</h4>
                  <div className="space-y-2">
                    {punchDetail.events.map((event, index) => (
                      <div key={event.id} className="flex items-center gap-3 p-2 rounded border border-neutral-200 bg-white">
                        <span className="w-6 text-xs text-neutral-400">{index + 1}</span>
                        <Badge status={event.type}>{event.type}</Badge>
                        <span className="font-medium text-neutral-900">{event.time}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-neutral-700 mb-2">Các cặp ra/vào</h4>
                  <div className="space-y-2">
                    {punchDetail.segments.map((segment) => (
                      <div key={segment.index} className="flex items-center justify-between p-2 rounded border border-neutral-200 bg-white text-sm">
                        <span className="text-neutral-600">
                          {segment.checkIn} → {segment.checkOut || <span className="text-warning-700">chưa quét ra</span>}
                        </span>
                        <span className="font-medium text-neutral-900">
                          {segment.checkOut ? `${segment.minutes} phút` : '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-neutral-500 mt-2">
                    Giờ công được tính từ lượt vào đầu tiên đến lượt ra cuối cùng: <strong>{punchDetail.record.workedMinutes ?? 0} phút</strong>.
                  </p>
                </div>
              </>
            )}

            <div className="flex justify-end pt-4 border-t">
              <Button variant="ghost" onClick={() => setPunchDetail(null)}>Đóng</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal duyệt tăng ca */}
      <Modal isOpen={!!overtimeRecord} onClose={() => setOvertimeRecord(null)} title="Duyệt giờ tăng ca">
        {overtimeRecord && (
          <div className="space-y-4 mt-4">
            <div className="bg-neutral-50 p-3 rounded-md border border-neutral-200 space-y-1">
              <p className="text-sm font-medium">Nhân viên: {overtimeRecord.employeeName} ({overtimeRecord.employeeCode})</p>
              <p className="text-sm text-neutral-500">Ngày: {overtimeRecord.date}</p>
              <p className="text-sm text-neutral-500">
                Check-out: {overtimeRecord.checkOutTime || '—'} · Tăng ca: <strong>{formatDuration(overtimeRecord.overtimeMinutes)}</strong>
              </p>
            </div>
            <Textarea
              label="Lý do"
              required
              value={overtimeReason}
              onChange={(e) => setOvertimeReason(e.target.value)}
              placeholder="Nhập lý do duyệt hoặc từ chối giờ tăng ca"
            />
            <p className="text-xs text-neutral-500">
              Chỉ giờ tăng ca đã duyệt mới được đưa vào sheet &quot;Công OT&quot; của báo cáo tháng.
            </p>
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
              <Button variant="ghost" onClick={() => setOvertimeRecord(null)}>Hủy</Button>
              <Button variant="danger" isLoading={overtimeBusy} onClick={() => handleDecideOvertime('REJECTED')} className="gap-2">
                <X className="w-4 h-4" /> Từ chối
              </Button>
              <Button isLoading={overtimeBusy} onClick={() => handleDecideOvertime('APPROVED')} className="gap-2">
                <Check className="w-4 h-4" /> Duyệt
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal lịch sử chỉnh sửa */}
      <Modal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        title="Lịch sử chỉnh sửa"
        panelClassName="max-w-[548px]"
      >
        <div className="mt-4 max-h-96 overflow-y-auto">
          {auditLoading ? (
            <div className="space-y-4">
              {[1, 2].map(i => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : auditLogs.length === 0 ? (
            <p className="text-neutral-500 text-sm text-center py-4">Bản ghi này chưa có chỉnh sửa nào.</p>
          ) : (
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-neutral-200 before:to-transparent">
              {auditLogs.map((log) => (
                <div key={log.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-4 h-4 rounded-full border border-white bg-primary-500 text-neutral-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2"></div>
                    <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] p-4 rounded border border-neutral-200 bg-white shadow-sm">
                        <div className="flex items-center justify-between space-x-2 mb-1">
                            <div className="font-bold text-neutral-900">{log.user}</div>
                            <time className="text-xs font-medium text-neutral-500">{new Date(log.timestamp).toLocaleString()}</time>
                        </div>
                        <div className="text-sm text-neutral-500 mb-2">Lý do: <span className="font-medium text-neutral-700">{log.reason}</span></div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-danger-50 p-2 rounded text-danger-700 border border-danger-100">
                            <span className="block font-semibold mb-1">Giá trị cũ:</span>
                            {Object.entries(log.oldValue).map(([k, v]) => (
                               v && k !== 'id' && k !== 'employeeId' ? <div key={k}>{k}: {v}</div> : null
                            ))}
                          </div>
                          <div className="bg-success-50 p-2 rounded text-success-700 border border-success-100">
                            <span className="block font-semibold mb-1">Giá trị mới:</span>
                            {Object.entries(log.newValue).map(([k, v]) => (
                               v && k !== 'id' && k !== 'employeeId' ? <div key={k}>{k}: {v}</div> : null
                            ))}
                          </div>
                        </div>
                    </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Attendance;
