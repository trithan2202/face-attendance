import React, { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Search, Plus, Edit2, Trash2, Camera } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Table from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Modal from '../../components/ui/Modal';
import { statusLabelVi } from '../../utils/statusLabels';

const employeeSchema = z.object({
  code: z.string().min(1, 'Vui lòng nhập mã nhân viên'),
  name: z.string().min(1, 'Vui lòng nhập họ tên'),
  email: z.union([z.string().email('Email không hợp lệ'), z.literal('')]),
  phone: z.union([
    z.string().regex(/^[0-9+\-\s]{8,30}$/, 'Số điện thoại không hợp lệ'),
    z.literal(''),
  ]),
  nationalId: z.union([
    z.string().regex(/^[0-9]{9,12}$/, 'CCCD phải là 9–12 chữ số'),
    z.literal(''),
  ]),
  departmentId: z.coerce.number().positive('Vui lòng chọn phòng ban'),
  shiftId: z.coerce.number().positive('Vui lòng chọn ca làm'),
  status: z.string().min(1, 'Vui lòng chọn trạng thái'),
});

const generateEmployeeCode = (employees) => {
  const existingCodes = new Set(employees.map(employee => employee.code.toUpperCase()));
  const randomValue = new Uint32Array(1);

  for (let attempt = 0; attempt < 100; attempt += 1) {
    const value = globalThis.crypto?.getRandomValues
      ? globalThis.crypto.getRandomValues(randomValue)[0] % 1_000_000
      : Math.floor(Math.random() * 1_000_000);
    const code = `A${String(value).padStart(6, '0')}`;
    if (!existingCodes.has(code)) return code;
  }

  for (let value = 0; value < 1_000_000; value += 1) {
    const code = `A${String(value).padStart(6, '0')}`;
    if (!existingCodes.has(code)) return code;
  }

  throw new Error('Không còn mã nhân viên khả dụng');
};

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDept, setFilterDept] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [deleteId, setDeleteId] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [enrollment, setEnrollment] = useState(null);
  const [enrollmentEmployee, setEnrollmentEmployee] = useState(null);
  const [enrollmentBusy, setEnrollmentBusy] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const { addToast } = useToast();

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(employeeSchema),
    defaultValues: { status: 'Pending enrollment' }
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [data, shiftData, departmentData] = await Promise.all([
        mockApi.employees.list(),
        mockApi.shifts.list(),
        mockApi.departments.list(),
      ]);
      setEmployees(data);
      setShifts(shiftData);
      setDepartments(departmentData);
    } catch (err) {
      addToast('Không thể tải danh sách nhân viên', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredEmployees = employees.filter(emp => {
    const matchSearch = emp.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                        emp.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchDept = filterDept ? String(emp.departmentId) === String(filterDept) : true;
    const matchStatus = filterStatus ? emp.status === filterStatus : true;
    return matchSearch && matchDept && matchStatus;
  });

  const handleOpenModal = (emp = null) => {
    if (emp) {
      setEditingId(emp.id);
      Object.keys(emp).forEach(key => setValue(key, emp[key]));
    } else {
      setEditingId(null);
      reset({
        code: generateEmployeeCode(employees),
        name: '',
        email: '',
        phone: '',
        nationalId: '',
        departmentId: '',
        shiftId: '',
        status: 'Pending enrollment',
      });
    }
    setIsModalOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      if (editingId) {
        await mockApi.employees.update(editingId, data);
        addToast('Cập nhật nhân viên thành công', 'success');
      } else {
        await mockApi.employees.create(data);
        addToast('Tạo nhân viên thành công', 'success');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Thao tác thất bại', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await mockApi.employees.delete(deleteId);
      addToast('Đã xóa nhân viên', 'success');
      setIsDeleteModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Không thể xóa nhân viên', 'error');
    }
  };

  const stopEnrollment = async (cancel = true) => {
    if (cancel && enrollment?.session_id && ['LIVENESS', 'CAPTURING'].includes(enrollment.state)) {
      try { await mockApi.employees.cancelEnrollment(enrollment.session_id); } catch { /* already closed */ }
    }
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    setEnrollment(null);
    setEnrollmentEmployee(null);
  };

  const handleResetFace = async (employee) => {
    try {
      const session = await mockApi.employees.startEnrollment(employee.id);
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      setEnrollmentEmployee(employee);
      setEnrollment(session);
      setTimeout(() => { if (videoRef.current) videoRef.current.srcObject = stream; }, 0);
    } catch (err) {
       addToast(err.message || 'Không thể bắt đầu đăng ký khuôn mặt', 'error');
    }
  };

  useEffect(() => () => streamRef.current?.getTracks().forEach(track => track.stop()), []);

  useEffect(() => {
    if (!enrollment?.session_id || !['LIVENESS', 'CAPTURING'].includes(enrollment.state)) return undefined;
    let stopped = false;
    const capture = async () => {
      if (stopped || enrollmentBusy || !videoRef.current?.videoWidth) return;
      setEnrollmentBusy(true);
      try {
        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.85));
        const result = await mockApi.employees.submitEnrollmentFrame(enrollment.session_id, blob);
        setEnrollment(result);
        if (result.state === 'COMPLETED') {
          streamRef.current?.getTracks().forEach(track => track.stop());
          addToast('Đăng ký khuôn mặt thành công', 'success');
          loadData();
        } else if (['FAILED', 'CANCELLED', 'EXPIRED'].includes(result.state)) {
          streamRef.current?.getTracks().forEach(track => track.stop());
          addToast(result.message || 'Đăng ký khuôn mặt thất bại', 'error');
        }
      } catch (err) {
        addToast(err.message || 'Không thể gửi khung hình đăng ký', 'error');
      } finally { setEnrollmentBusy(false); }
    };
    const timer = setInterval(capture, 650);
    return () => { stopped = true; clearInterval(timer); };
  }, [enrollment?.session_id, enrollment?.state, enrollmentBusy]);

  const columns = [
    { header: 'Mã NV', cell: (row) => <span className="font-medium text-neutral-900">{row.code}</span> },
    { header: 'Họ tên', cell: (row) => (
      <span className="block max-w-[150px] truncate font-medium text-neutral-900" title={row.name}>{row.name}</span>
    )},
    { header: 'Email', cell: (row) => (
      row.email
        ? <span className="block max-w-[160px] truncate" title={row.email}>{row.email}</span>
        : <span className="text-neutral-400">—</span>
    )},
    { header: 'Số điện thoại', cell: (row) => row.phone || <span className="text-neutral-400">—</span> },
    { header: 'CCCD', cell: (row) => row.nationalId || <span className="text-neutral-400">—</span> },
    { header: 'Phòng ban', cell: (row) => (
      <span className="block max-w-[110px] truncate" title={row.department}>{row.department || '—'}</span>
    )},
    { header: 'Ca làm', cell: (row) => (
      <span className="block max-w-[100px] truncate" title={row.shift}>{row.shift}</span>
    )},
    { header: 'Trạng thái', cell: (row) => <Badge status={row.status}>{statusLabelVi(row.status)}</Badge> },
    { header: 'Thao tác', cell: (row) => (
      <div className="flex gap-1">
        <button onClick={() => handleOpenModal(row)} className="p-1 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Sửa">
          <Edit2 className="w-3.5 h-3.5" />
        </button>
        <button onClick={() => { setDeleteId(row.id); setIsDeleteModalOpen(true); }} className="p-1 text-danger-500 rounded" title="Xóa">
          <Trash2 className="w-3.5 h-3.5" />
        </button>
        <button onClick={() => handleResetFace(row)} className="p-1 text-neutral-500 hover:text-warning-600 hover:bg-warning-50 rounded" title="Đăng ký khuôn mặt">
          <Camera className="w-3.5 h-3.5" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-neutral-900">Nhân viên</h1>
        <Button onClick={() => handleOpenModal()} className="gap-2">
          <Plus className="w-4 h-4" /> Thêm nhân viên
        </Button>
      </div>

      <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm flex flex-col sm:flex-row gap-4">
        <Input
          placeholder="Tìm theo tên hoặc mã nhân viên..."
          icon={Search}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-xs"
        />
        <Select
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
          options={departments.map(item => ({ value: item.id, label: item.name }))}
          className="max-w-xs"
        />
        <Select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          options={[
            { value: 'Active', label: 'Đang hoạt động' },
            { value: 'Inactive', label: 'Ngưng hoạt động' },
            { value: 'Pending enrollment', label: 'Chờ đăng ký khuôn mặt' }
          ]}
          className="max-w-xs"
        />
      </div>

      <Table columns={columns} data={filteredEmployees} isLoading={loading} dense />

      {/* Modal Thêm/Sửa */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Sửa nhân viên' : 'Thêm nhân viên'}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          <Input label="Mã nhân viên" {...register('code')} error={errors.code?.message} disabled={!!editingId} />
          <Input label="Họ tên" {...register('name')} error={errors.name?.message} />
          <Input label="Địa chỉ email" type="email" {...register('email')} error={errors.email?.message} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Số điện thoại" {...register('phone')} error={errors.phone?.message} placeholder="VD: 0900000000" />
            <Input label="Số CCCD" {...register('nationalId')} error={errors.nationalId?.message} placeholder="VD: 001234567890" />
          </div>
          <Select
            label="Phòng ban"
            {...register('departmentId')}
            error={errors.departmentId?.message}
            options={departments.map(item => ({ value: item.id, label: item.name }))}
          />
          <Select
            label="Ca làm"
            {...register('shiftId')}
            error={errors.shiftId?.message}
            options={shifts.map(item => ({ value: item.id, label: `${item.code} — ${item.name}` }))}
          />
          {editingId && <Select label="Trạng thái" {...register('status')} options={[
            { value: 'Active', label: 'Đang hoạt động' }, { value: 'Inactive', label: 'Ngưng hoạt động' },
            { value: 'Pending enrollment', label: 'Chờ đăng ký khuôn mặt' },
          ]} />}

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Hủy</Button>
            <Button type="submit" isLoading={isSubmitting}>Lưu</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={!!enrollmentEmployee} onClose={() => stopEnrollment(true)} title="Đăng ký khuôn mặt">
        <div className="space-y-4 mt-4">
          <p className="text-sm text-neutral-600">
            {enrollmentEmployee?.name}:{' '}
            {enrollment?.state === 'LIVENESS'
              ? enrollment?.liveness_instruction
              : 'giữ khuôn mặt rõ nét và thay đổi góc mặt nhẹ.'}
          </p>
          <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-video bg-neutral-900 rounded-lg object-cover -scale-x-100" />
          <div className="flex justify-between text-sm">
            <span>{enrollment?.message}</span>
            <strong>
              {enrollment?.state === 'LIVENESS'
                ? 'Kiểm tra liveness'
                : `${enrollment?.samples_collected || 0}/${enrollment?.target_samples || 5}`}
            </strong>
          </div>
          <div className="h-2 bg-neutral-200 rounded overflow-hidden">
            <div
              className="h-full bg-primary-600 transition-all"
              style={{
                width: enrollment?.state === 'LIVENESS'
                  ? `${Math.min(100, ((enrollment?.liveness_progress || 0) / (enrollment?.liveness_required_progress || 3)) * 100)}%`
                  : `${((enrollment?.samples_collected || 0) / (enrollment?.target_samples || 5)) * 100}%`,
              }}
            />
          </div>
          <div className="flex justify-end"><Button variant="ghost" onClick={() => stopEnrollment(enrollment?.state !== 'COMPLETED')}>Đóng</Button></div>
        </div>
      </Modal>

      {/* Modal xác nhận xóa */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Xóa nhân viên">
        <div className="mt-4">
          <p className="text-neutral-600">Bạn có chắc chắn muốn xóa nhân viên này? Hành động này không thể hoàn tác.</p>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>Hủy</Button>
            <Button variant="danger" onClick={handleDelete}>Xóa</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Employees;
