import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { AlertCircle, CalendarSearch, IdCard, CreditCard, ArrowLeft } from 'lucide-react';
import { api } from '../../services/api';
import { formatDuration } from '../../utils/duration';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Table from '../../components/ui/Table';
import { statusLabelVi } from '../../utils/statusLabels';

const lookupSchema = z.object({
  employeeCode: z.string().min(1, 'Vui lòng nhập mã nhân viên'),
  nationalId: z.string().regex(/^[0-9]{9,12}$/, 'CCCD phải là 9–12 chữ số'),
  month: z.string().min(1, 'Vui lòng chọn tháng'),
});

const StatCard = ({ label, value }) => (
  <div className="bg-white p-4 rounded-lg border border-neutral-200">
    <p className="text-xs font-medium text-neutral-500 mb-1">{label}</p>
    <p className="text-xl font-bold text-neutral-900">{value}</p>
  </div>
);

const Lookup = () => {
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(lookupSchema),
    defaultValues: { employeeCode: '', nationalId: '', month: new Date().toISOString().slice(0, 7) }
  });

  const onSubmit = async (data) => {
    try {
      setError('');
      setResult(null);
      const found = await api.public.lookupAttendance(data);
      setResult(found);
    } catch (err) {
      setError(err.message || 'Không thể tra cứu, vui lòng thử lại');
    }
  };

  const columns = [
    { header: 'Ngày', accessorKey: 'date' },
    { header: 'Check-in', cell: (row) => row.checkIn || '—' },
    { header: 'Check-out', cell: (row) => row.checkOut || '—' },
    { header: 'Phút làm', accessorKey: 'workedMinutes' },
    { header: 'Đi trễ', cell: (row) => (row.lateMinutes ? `${row.lateMinutes} phút` : '—') },
    { header: 'Trạng thái', cell: (row) => <Badge status={row.status}>{statusLabelVi(row.status)}</Badge> },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 py-10 px-4 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <CalendarSearch className="w-7 h-7 text-primary-600" />
          </div>
          <h1 className="text-2xl font-bold text-neutral-900">Tra cứu chấm công</h1>
          <p className="text-neutral-500 mt-2 text-sm">
            Nhập mã nhân viên và số CCCD đã đăng ký để xem bảng công của bạn.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-card p-6">
          {error && (
            <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-md flex items-start gap-3 text-danger-700">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span className="text-sm font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col sm:flex-row gap-4 items-end">
            <Input
              label="Mã nhân viên"
              placeholder="VD: NV001"
              icon={IdCard}
              error={errors.employeeCode?.message}
              {...register('employeeCode')}
            />
            <Input
              label="Số CCCD"
              placeholder="VD: 001234567890"
              icon={CreditCard}
              error={errors.nationalId?.message}
              {...register('nationalId')}
            />
            <Input
              label="Tháng"
              type="month"
              error={errors.month?.message}
              {...register('month')}
            />
            <Button type="submit" isLoading={isSubmitting} className="mb-[2px] shrink-0">
              Tra cứu
            </Button>
          </form>
        </div>

        {result && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-card p-6">
              <h2 className="text-lg font-bold text-neutral-900">{result.fullName}</h2>
              <p className="text-sm text-neutral-500 mt-1">
                {result.employeeCode}
                {result.department && ` · ${result.department}`}
                {result.shiftCode && ` · Ca ${result.shiftCode}`}
                {` · Tháng ${result.month}`}
              </p>

              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mt-5">
                <StatCard label="Ngày công" value={result.summary.presentDays} />
                <StatCard label="Ngày nghỉ phép" value={result.summary.leaveDays} />
                <StatCard label="Số lần đi trễ" value={result.summary.lateDays} />
                <StatCard label="Tổng giờ làm" value={`${Math.floor(result.summary.totalWorkedMinutes / 60)}h`} />
                <StatCard label="Tăng ca đã duyệt" value={formatDuration(result.summary.approvedOvertimeMinutes)} />
              </div>
            </div>

            <Table
              columns={columns}
              data={result.days}
              emptyMessage="Không có dữ liệu chấm công trong tháng này."
            />
          </div>
        )}

        <div className="text-center">
          <a href="/login" className="text-sm text-neutral-500 hover:text-primary-600 inline-flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> Đăng nhập trang quản trị
          </a>
        </div>
      </div>
    </div>
  );
};

export default Lookup;
