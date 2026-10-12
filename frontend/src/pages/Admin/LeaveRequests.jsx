import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Plus, Check, X, Trash2, Mail, MailCheck, MailX, RotateCw } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Table from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Combobox from '../../components/ui/Combobox';
import Textarea from '../../components/ui/Textarea';
import Modal from '../../components/ui/Modal';
import { statusLabelVi } from '../../utils/statusLabels';

const leaveSchema = z.object({
  employeeId: z.coerce.number().positive('Vui lòng chọn nhân viên'),
  leaveType: z.string().min(1, 'Vui lòng chọn loại nghỉ phép'),
  startDate: z.string().min(1, 'Vui lòng chọn ngày bắt đầu'),
  endDate: z.string().min(1, 'Vui lòng chọn ngày kết thúc'),
  reason: z.string().min(3, 'Lý do phải có ít nhất 3 ký tự'),
}).refine(data => data.endDate >= data.startDate, {
  message: 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu',
  path: ['endDate'],
});

const LEAVE_TYPES = [
  { value: 'ANNUAL', label: 'Nghỉ phép năm' },
  { value: 'SICK', label: 'Nghỉ ốm' },
  { value: 'UNPAID', label: 'Nghỉ không lương' },
  { value: 'OTHER', label: 'Khác' },
];

// Thời điểm từ API là UTC không kèm múi giờ.
const formatSentAt = (value) => (value
  ? new Date(`${value}Z`).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' })
  : '');

const EMAIL_STATUS = {
  SENT: { label: 'Đã gửi', icon: MailCheck, className: 'bg-success-100 text-success-700' },
  FAILED: { label: 'Gửi lỗi', icon: MailX, className: 'bg-danger-100 text-danger-700' },
  NO_EMAIL: { label: 'Không có email', icon: MailX, className: 'bg-warning-100 text-warning-700' },
  NOT_CONFIGURED: { label: 'Chưa cấu hình', icon: MailX, className: 'bg-warning-100 text-warning-700' },
};

const EmailStatus = ({ row, onResend, busy }) => {
  if (row.rawStatus !== 'APPROVED') {
    return <span className="text-xs text-neutral-400">—</span>;
  }
  const config = EMAIL_STATUS[row.emailStatus] || { label: 'Chưa gửi', icon: Mail, className: 'bg-neutral-100 text-neutral-600' };
  const Icon = config.icon;
  const title = row.emailStatus === 'SENT' ? `Gửi lúc ${formatSentAt(row.emailSentAt)}` : row.emailError || '';
  return (
    <div className="flex items-center gap-1.5">
      <span title={title} className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${config.className}`}>
        <Icon className="w-3.5 h-3.5" /> {config.label}
      </span>
      <button
        onClick={() => onResend(row)}
        disabled={busy}
        className="p-1 text-neutral-400 hover:text-primary-600 hover:bg-primary-50 rounded disabled:opacity-50"
        title={row.emailStatus === 'SENT' ? 'Gửi lại email' : 'Thử gửi lại email'}
      >
        <RotateCw className={`w-3.5 h-3.5 ${busy ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
};

const EMAIL_TOAST = {
  SENT: ['Đã gửi email thông báo cho nhân viên', 'success'],
  FAILED: ['Đã duyệt đơn nhưng gửi email thất bại, có thể gửi lại ở cột Email', 'error'],
  NO_EMAIL: ['Đã duyệt đơn; nhân viên chưa có email nên không gửi thông báo', 'warning'],
  NOT_CONFIGURED: ['Đã duyệt đơn; chưa cấu hình SMTP nên không gửi email', 'warning'],
};

const LeaveRequests = () => {
  const [requests, setRequests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('All');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [decision, setDecision] = useState(null);
  const [decisionNote, setDecisionNote] = useState('');
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [resendingId, setResendingId] = useState(null);

  const { addToast } = useToast();

  const { register, handleSubmit, reset, setValue, watch, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(leaveSchema),
    defaultValues: { employeeId: '', leaveType: 'ANNUAL', startDate: '', endDate: '', reason: '' }
  });

  const selectedEmployeeId = watch('employeeId');

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await mockApi.leave.list({ status: filterStatus });
      setRequests(data);
    } catch (err) {
      addToast('Không thể tải danh sách đơn nghỉ phép', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  useEffect(() => {
    mockApi.employees.list()
      .then(setEmployees)
      .catch(() => addToast('Không thể tải danh sách nhân viên', 'error'));
  }, []);

  const handleOpenModal = () => {
    reset({ employeeId: '', leaveType: 'ANNUAL', startDate: '', endDate: '', reason: '' });
    setIsModalOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      await mockApi.leave.create(data);
      addToast('Tạo đơn nghỉ phép thành công', 'success');
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast(err.message || 'Thao tác thất bại', 'error');
    }
  };

  const handleDecide = async (status) => {
    setDecisionBusy(true);
    try {
      const result = await mockApi.leave.decide(decision.id, status, decisionNote);
      if (status === 'APPROVED') {
        const skipped = result.skipped_days
          ? ` (${result.skipped_days} ngày đã có chấm công nên được giữ nguyên)`
          : '';
        addToast(`Đã duyệt đơn, ghi nhận ${result.applied_days} ngày nghỉ${skipped}`, 'success');
        const [message, type] = EMAIL_TOAST[result.email_status] || [];
        if (message) addToast(message, type);
      } else {
        addToast('Đã từ chối đơn nghỉ phép', 'success');
      }
      setDecision(null);
      setDecisionNote('');
      loadData();
    } catch (err) {
      addToast(err.message || 'Thao tác thất bại', 'error');
    } finally {
      setDecisionBusy(false);
    }
  };

  const handleResendEmail = async (row) => {
    setResendingId(row.id);
    try {
      const updated = await mockApi.leave.resendEmail(row.id);
      setRequests((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      const [message, type] = EMAIL_TOAST[updated.emailStatus] || [];
      addToast(
        updated.emailStatus === 'SENT' ? 'Đã gửi lại email thông báo' : (updated.emailError || message),
        updated.emailStatus === 'SENT' ? 'success' : type || 'error',
      );
    } catch (err) {
      addToast(err.message || 'Không thể gửi email', 'error');
    } finally {
      setResendingId(null);
    }
  };

  const handleDelete = async () => {
    try {
      await mockApi.leave.delete(deleteId);
      addToast('Đã xóa đơn nghỉ phép', 'success');
      setIsDeleteModalOpen(false);
      loadData();
    } catch (err) {
      addToast(err.message || 'Không thể xóa đơn nghỉ phép', 'error');
    }
  };

  const columns = [
    { header: 'Nhân viên', cell: (row) => (
      <div>
        <div className="font-medium text-neutral-900">{row.employeeName}</div>
        <div className="text-xs text-neutral-500">{row.employeeCode}</div>
      </div>
    )},
    { header: 'Loại nghỉ', accessorKey: 'leaveTypeLabel' },
    { header: 'Từ ngày', accessorKey: 'startDate' },
    { header: 'Đến ngày', accessorKey: 'endDate' },
    { header: 'Số ngày', accessorKey: 'totalDays' },
    { header: 'Lý do', cell: (row) => (
      <span className="block max-w-[220px] truncate" title={row.reason}>{row.reason}</span>
    )},
    { header: 'Trạng thái', cell: (row) => <Badge status={row.status}>{statusLabelVi(row.status)}</Badge> },
    { header: 'Email thông báo', cell: (row) => (
      <EmailStatus row={row} onResend={handleResendEmail} busy={resendingId === row.id} />
    )},
    { header: 'Thao tác', cell: (row) => (
      <div className="flex gap-2">
        {row.rawStatus === 'PENDING' && (
          <>
            <button onClick={() => { setDecision(row); setDecisionNote(''); }} className="p-1.5 text-neutral-500 hover:text-success-700 hover:bg-success-50 rounded" title="Duyệt / Từ chối">
              <Check className="w-4 h-4" />
            </button>
            <button onClick={() => { setDeleteId(row.id); setIsDeleteModalOpen(true); }} className="p-1.5 text-danger-500 rounded" title="Xóa">
              <Trash2 className="w-4 h-4" />
            </button>
          </>
        )}
        {row.rawStatus !== 'PENDING' && (
          <span className="text-xs text-neutral-400">Đã xử lý</span>
        )}
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-neutral-900">Nghỉ phép</h1>
        <Button onClick={handleOpenModal} className="gap-2">
          <Plus className="w-4 h-4" /> Tạo đơn nghỉ phép
        </Button>
      </div>

      <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm flex flex-col sm:flex-row gap-4 items-end">
        <Select
          label="Trạng thái"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          options={[
            { value: 'All', label: 'Tất cả trạng thái' },
            { value: 'Pending', label: 'Chờ duyệt' },
            { value: 'Approved', label: 'Đã duyệt' },
            { value: 'Rejected', label: 'Từ chối' },
          ]}
          className="max-w-[200px]"
        />
      </div>

      <Table columns={columns} data={requests} isLoading={loading} emptyMessage="Chưa có đơn nghỉ phép nào." />

      {/* Modal tạo đơn */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Tạo đơn nghỉ phép">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          <Combobox
            label="Nhân viên"
            placeholder="Gõ mã hoặc tên nhân viên để tìm..."
            emptyMessage="Không tìm thấy nhân viên phù hợp"
            error={errors.employeeId?.message}
            value={selectedEmployeeId}
            onChange={(value) => setValue('employeeId', value, { shouldValidate: true })}
            options={employees.map(item => ({
              value: item.id,
              label: item.name,
              hint: `${item.code}${item.department ? ` · ${item.department}` : ''}`,
            }))}
          />
          <Select
            label="Loại nghỉ phép"
            {...register('leaveType')}
            error={errors.leaveType?.message}
            options={LEAVE_TYPES}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Từ ngày" type="date" {...register('startDate')} error={errors.startDate?.message} />
            <Input label="Đến ngày" type="date" {...register('endDate')} error={errors.endDate?.message} />
          </div>
          <Textarea label="Lý do" required {...register('reason')} error={errors.reason?.message} placeholder="Nhập lý do xin nghỉ" />

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Hủy</Button>
            <Button type="submit" isLoading={isSubmitting}>Lưu</Button>
          </div>
        </form>
      </Modal>

      {/* Modal duyệt/từ chối */}
      <Modal isOpen={!!decision} onClose={() => setDecision(null)} title="Xử lý đơn nghỉ phép">
        {decision && (
          <div className="space-y-4 mt-4">
            <div className="bg-neutral-50 p-3 rounded-md border border-neutral-200 space-y-1">
              <p className="text-sm font-medium">Nhân viên: {decision.employeeName} ({decision.employeeCode})</p>
              <p className="text-sm text-neutral-500">{decision.leaveTypeLabel}: {decision.startDate} → {decision.endDate} ({decision.totalDays} ngày)</p>
              <p className="text-sm text-neutral-500">Lý do: {decision.reason}</p>
            </div>
            <Textarea
              label="Ghi chú xử lý"
              value={decisionNote}
              onChange={(e) => setDecisionNote(e.target.value)}
              placeholder="Ghi chú (không bắt buộc)"
            />
            <p className="text-xs text-neutral-500">
              Khi duyệt, các ngày trong khoảng (trừ Chủ nhật) sẽ được ghi nhận là nghỉ phép.
              Ngày đã có dữ liệu chấm công thực tế sẽ được giữ nguyên.
              Khi duyệt, hệ thống gửi email thông báo đến nhân viên.
            </p>
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
              <Button variant="ghost" onClick={() => setDecision(null)}>Hủy</Button>
              <Button variant="danger" isLoading={decisionBusy} onClick={() => handleDecide('REJECTED')} className="gap-2">
                <X className="w-4 h-4" /> Từ chối
              </Button>
              <Button isLoading={decisionBusy} onClick={() => handleDecide('APPROVED')} className="gap-2">
                <Check className="w-4 h-4" /> Duyệt
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal xác nhận xóa */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Xóa đơn nghỉ phép">
        <div className="mt-4">
          <p className="text-neutral-600">Bạn có chắc chắn muốn xóa đơn nghỉ phép này? Hành động này không thể hoàn tác.</p>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>Hủy</Button>
            <Button variant="danger" onClick={handleDelete}>Xóa</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default LeaveRequests;
