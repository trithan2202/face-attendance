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

const employeeSchema = z.object({
  code: z.string().min(1, 'Code is required'),
  name: z.string().min(1, 'Name is required'),
  email: z.union([z.string().email('Invalid email'), z.literal('')]),
  department: z.string().min(1, 'Department is required'),
  shiftId: z.coerce.number().positive('Shift is required'),
  status: z.string().min(1, 'Status is required'),
});

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [shifts, setShifts] = useState([]);
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
      const [data, shiftData] = await Promise.all([mockApi.employees.list(), mockApi.shifts.list()]);
      setEmployees(data);
      setShifts(shiftData);
    } catch (err) {
      addToast('Failed to load employees', 'error');
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
    const matchDept = filterDept ? emp.department === filterDept : true;
    const matchStatus = filterStatus ? emp.status === filterStatus : true;
    return matchSearch && matchDept && matchStatus;
  });

  const handleOpenModal = (emp = null) => {
    if (emp) {
      setEditingId(emp.id);
      Object.keys(emp).forEach(key => setValue(key, emp[key]));
    } else {
      setEditingId(null);
      reset({ status: 'Pending enrollment' });
    }
    setIsModalOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      if (editingId) {
        await mockApi.employees.update(editingId, data);
        addToast('Employee updated successfully', 'success');
      } else {
        await mockApi.employees.create(data);
        addToast('Employee created successfully', 'success');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Operation failed', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await mockApi.employees.delete(deleteId);
      addToast('Employee deleted', 'success');
      setIsDeleteModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Failed to delete employee', 'error');
    }
  };

  const stopEnrollment = async (cancel = true) => {
    if (cancel && enrollment?.session_id && enrollment.state === 'CAPTURING') {
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
    if (!enrollment?.session_id || enrollment.state !== 'CAPTURING') return undefined;
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
        }
      } catch (err) {
        addToast(err.message || 'Không thể gửi frame enrollment', 'error');
      } finally { setEnrollmentBusy(false); }
    };
    const timer = setInterval(capture, 650);
    return () => { stopped = true; clearInterval(timer); };
  }, [enrollment?.session_id, enrollment?.state, enrollmentBusy]);

  const columns = [
    { header: 'Code', accessorKey: 'code' },
    { header: 'Name', accessorKey: 'name' },
    { header: 'Email', accessorKey: 'email' },
    { header: 'Department', accessorKey: 'department' },
    { header: 'Shift', accessorKey: 'shift' },
    { header: 'Status', cell: (row) => <Badge status={row.status}>{row.status}</Badge> },
    { header: 'Actions', cell: (row) => (
      <div className="flex gap-2">
        <button onClick={() => handleOpenModal(row)} className="p-1.5 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Edit">
          <Edit2 className="w-4 h-4" />
        </button>
        <button onClick={() => { setDeleteId(row.id); setIsDeleteModalOpen(true); }} className="p-1.5 text-neutral-500 hover:text-danger-600 hover:bg-danger-50 rounded" title="Delete">
          <Trash2 className="w-4 h-4" />
        </button>
        <button onClick={() => handleResetFace(row)} className="p-1.5 text-neutral-500 hover:text-warning-600 hover:bg-warning-50 rounded" title="Register Face">
          <Camera className="w-4 h-4" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-neutral-900">Employees</h1>
        <Button onClick={() => handleOpenModal()} className="gap-2">
          <Plus className="w-4 h-4" /> Add Employee
        </Button>
      </div>

      <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm flex flex-col sm:flex-row gap-4">
        <Input 
          placeholder="Search name or code..." 
          icon={Search} 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-xs"
        />
        <Select 
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
          options={[
            { value: 'Engineering', label: 'Engineering' },
            { value: 'HR', label: 'HR' },
            { value: 'Sales', label: 'Sales' }
          ]}
          className="max-w-xs"
        />
        <Select 
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          options={[
            { value: 'Active', label: 'Active' },
            { value: 'Inactive', label: 'Inactive' },
            { value: 'Pending enrollment', label: 'Pending enrollment' }
          ]}
          className="max-w-xs"
        />
      </div>

      <Table columns={columns} data={filteredEmployees} isLoading={loading} />

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Edit Employee' : 'Add Employee'}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          <Input label="Employee Code" {...register('code')} error={errors.code?.message} disabled={!!editingId} />
          <Input label="Full Name" {...register('name')} error={errors.name?.message} />
          <Input label="Email Address" type="email" {...register('email')} error={errors.email?.message} />
          <Select 
            label="Department" 
            {...register('department')} 
            error={errors.department?.message}
            options={[
              { value: 'Engineering', label: 'Engineering' },
              { value: 'HR', label: 'HR' },
              { value: 'Sales', label: 'Sales' }
            ]}
          />
          <Select
            label="Shift" 
            {...register('shiftId')}
            error={errors.shiftId?.message}
            options={shifts.map(item => ({ value: item.id, label: `${item.code} — ${item.name}` }))}
          />
          {editingId && <Select label="Status" {...register('status')} options={[
            { value: 'Active', label: 'Active' }, { value: 'Inactive', label: 'Inactive' },
            { value: 'Pending enrollment', label: 'Pending enrollment' },
          ]} />}
          
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button type="submit" isLoading={isSubmitting}>Save</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={!!enrollmentEmployee} onClose={() => stopEnrollment(true)} title="Face enrollment">
        <div className="space-y-4 mt-4">
          <p className="text-sm text-neutral-600">{enrollmentEmployee?.name}: giữ một khuôn mặt rõ nét và thay đổi nhẹ góc nhìn.</p>
          <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-video bg-neutral-900 rounded-lg object-cover" />
          <div className="flex justify-between text-sm">
            <span>{enrollment?.message}</span>
            <strong>{enrollment?.samples_collected || 0}/{enrollment?.target_samples || 10}</strong>
          </div>
          <div className="h-2 bg-neutral-200 rounded overflow-hidden"><div className="h-full bg-primary-600" style={{ width: `${((enrollment?.samples_collected || 0) / 10) * 100}%` }} /></div>
          <div className="flex justify-end"><Button variant="ghost" onClick={() => stopEnrollment(enrollment?.state !== 'COMPLETED')}>Close</Button></div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Employee">
        <div className="mt-4">
          <p className="text-neutral-600">Are you sure you want to delete this employee? This action cannot be undone.</p>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete}>Delete</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Employees;
