import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Table from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';

const shiftSchema = z.object({
  code: z.string().min(1, 'Vui lòng nhập mã ca'),
  name: z.string().min(1, 'Vui lòng nhập tên ca'),
  startTime: z.string().min(1, 'Vui lòng nhập giờ bắt đầu'),
  endTime: z.string().min(1, 'Vui lòng nhập giờ kết thúc'),
  gracePeriod: z.coerce.number().min(0, 'Thời gian ân hạn phải >= 0'),
  overnight: z.boolean().default(false),
}).refine(data => {
  if (data.overnight) return true;
  return data.startTime < data.endTime;
}, {
  message: "Giờ kết thúc phải sau giờ bắt đầu (trừ ca qua đêm)",
  path: ["endTime"],
});

const Shifts = () => {
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [deleteId, setDeleteId] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const { addToast } = useToast();

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(shiftSchema),
    defaultValues: { overnight: false, gracePeriod: 15 }
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await mockApi.shifts.list();
      setShifts(data);
    } catch (err) {
      addToast('Không thể tải danh sách ca làm', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenModal = (shift = null) => {
    if (shift) {
      setEditingId(shift.id);
      Object.keys(shift).forEach(key => setValue(key, shift[key]));
    } else {
      setEditingId(null);
      reset({ overnight: false, gracePeriod: 15 });
    }
    setIsModalOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      if (editingId) {
        await mockApi.shifts.update(editingId, data);
        addToast('Cập nhật ca làm thành công', 'success');
      } else {
        await mockApi.shifts.create(data);
        addToast('Tạo ca làm thành công', 'success');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Thao tác thất bại', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await mockApi.shifts.delete(deleteId);
      addToast('Đã xóa ca làm', 'success');
      setIsDeleteModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Không thể xóa ca làm', 'error');
    }
  };

  const columns = [
    { header: 'Mã ca', accessorKey: 'code' },
    { header: 'Tên ca', accessorKey: 'name' },
    { header: 'Giờ bắt đầu', accessorKey: 'startTime' },
    { header: 'Giờ kết thúc', accessorKey: 'endTime' },
    { header: 'Thời gian ân hạn (phút)', accessorKey: 'gracePeriod' },
    { header: 'Qua đêm', cell: (row) => <Badge status={row.overnight ? 'Active' : 'Inactive'}>{row.overnight ? 'Có' : 'Không'}</Badge> },
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
        <h1 className="text-2xl font-bold text-neutral-900">Ca làm</h1>
        <Button onClick={() => handleOpenModal()} className="gap-2">
          <Plus className="w-4 h-4" /> Thêm ca làm
        </Button>
      </div>

      <Table columns={columns} data={shifts} isLoading={loading} />

      {/* Modal Thêm/Sửa */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Sửa ca làm' : 'Thêm ca làm'}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          <Input label="Mã ca" {...register('code')} error={errors.code?.message} disabled={!!editingId} />
          <Input label="Tên ca" {...register('name')} error={errors.name?.message} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Giờ bắt đầu" type="time" {...register('startTime')} error={errors.startTime?.message} />
            <Input label="Giờ kết thúc" type="time" {...register('endTime')} error={errors.endTime?.message} />
          </div>
          <Input label="Thời gian ân hạn (phút)" type="number" {...register('gracePeriod')} error={errors.gracePeriod?.message} />

          <div className="flex items-center gap-2 mt-2">
            <input type="checkbox" id="overnight" className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              {...register('overnight')}
            />
            <label htmlFor="overnight" className="text-sm text-neutral-700">Ca qua đêm</label>
          </div>

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Hủy</Button>
            <Button type="submit" isLoading={isSubmitting}>Lưu</Button>
          </div>
        </form>
      </Modal>

      {/* Modal xác nhận xóa */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Xóa ca làm">
        <div className="mt-4">
          <p className="text-neutral-600">Bạn có chắc chắn muốn xóa ca làm này? Hành động này không thể hoàn tác.</p>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>Hủy</Button>
            <Button variant="danger" onClick={handleDelete}>Xóa</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Shifts;
