import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Table from '../../components/ui/Table';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';

const departmentSchema = z.object({
  code: z.string().min(1, 'Vui lòng nhập mã phòng ban')
    .regex(/^[A-Za-z0-9_-]+$/, 'Mã chỉ gồm chữ, số, gạch ngang hoặc gạch dưới'),
  name: z.string().min(1, 'Vui lòng nhập tên phòng ban'),
  managerName: z.string().optional(),
});

const Departments = () => {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const [deleteId, setDeleteId] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const { addToast } = useToast();

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(departmentSchema),
    defaultValues: { code: '', name: '', managerName: '' }
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await mockApi.departments.list();
      setDepartments(data);
    } catch (err) {
      addToast('Không thể tải danh sách phòng ban', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenModal = (department = null) => {
    if (department) {
      setEditingId(department.id);
      Object.keys(department).forEach(key => setValue(key, department[key]));
    } else {
      setEditingId(null);
      reset({ code: '', name: '', managerName: '' });
    }
    setIsModalOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      if (editingId) {
        await mockApi.departments.update(editingId, data);
        addToast('Cập nhật phòng ban thành công', 'success');
      } else {
        await mockApi.departments.create(data);
        addToast('Tạo phòng ban thành công', 'success');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast(err.message || 'Thao tác thất bại', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await mockApi.departments.delete(deleteId);
      addToast('Đã xóa phòng ban', 'success');
      setIsDeleteModalOpen(false);
      loadData();
    } catch (err) {
      addToast(err.message || 'Không thể xóa phòng ban', 'error');
    }
  };

  const columns = [
    { header: 'Mã phòng ban', accessorKey: 'code' },
    { header: 'Tên phòng ban', accessorKey: 'name' },
    { header: 'Trưởng phòng', cell: (row) => row.managerName || '—' },
    { header: 'Số nhân viên', accessorKey: 'employeeCount' },
    { header: 'Thao tác', cell: (row) => (
      <div className="flex gap-2">
        <button onClick={() => handleOpenModal(row)} className="p-1.5 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Sửa">
          <Edit2 className="w-4 h-4" />
        </button>
        <button onClick={() => { setDeleteId(row.id); setIsDeleteModalOpen(true); }} className="p-1.5 text-danger-500 rounded" title="Xóa">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-neutral-900">Phòng ban</h1>
        <Button onClick={() => handleOpenModal()} className="gap-2">
          <Plus className="w-4 h-4" /> Thêm phòng ban
        </Button>
      </div>

      <Table columns={columns} data={departments} isLoading={loading} emptyMessage="Chưa có phòng ban nào." />

      {/* Modal Thêm/Sửa */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Sửa phòng ban' : 'Thêm phòng ban'}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          <Input label="Mã phòng ban" {...register('code')} error={errors.code?.message} disabled={!!editingId} />
          <Input label="Tên phòng ban" {...register('name')} error={errors.name?.message} />
          <Input label="Trưởng phòng" {...register('managerName')} error={errors.managerName?.message} />

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Hủy</Button>
            <Button type="submit" isLoading={isSubmitting}>Lưu</Button>
          </div>
        </form>
      </Modal>

      {/* Modal xác nhận xóa */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Xóa phòng ban">
        <div className="mt-4">
          <p className="text-neutral-600">Bạn có chắc chắn muốn xóa phòng ban này? Hành động này không thể hoàn tác.</p>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>Hủy</Button>
            <Button variant="danger" onClick={handleDelete}>Xóa</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Departments;
