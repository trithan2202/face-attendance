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
  code: z.string().min(1, 'Code is required'),
  name: z.string().min(1, 'Name is required'),
  startTime: z.string().min(1, 'Start time is required'),
  endTime: z.string().min(1, 'End time is required'),
  gracePeriod: z.coerce.number().min(0, 'Grace period must be >= 0'),
  overnight: z.boolean().default(false),
}).refine(data => {
  if (data.overnight) return true;
  return data.startTime < data.endTime;
}, {
  message: "End time must be after start time unless overnight",
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
      addToast('Failed to load shifts', 'error');
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
        addToast('Shift updated successfully', 'success');
      } else {
        await mockApi.shifts.create(data);
        addToast('Shift created successfully', 'success');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Operation failed', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await mockApi.shifts.delete(deleteId);
      addToast('Shift deleted', 'success');
      setIsDeleteModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Failed to delete shift', 'error');
    }
  };

  const columns = [
    { header: 'Code', accessorKey: 'code' },
    { header: 'Name', accessorKey: 'name' },
    { header: 'Start Time', accessorKey: 'startTime' },
    { header: 'End Time', accessorKey: 'endTime' },
    { header: 'Grace Period (min)', accessorKey: 'gracePeriod' },
    { header: 'Overnight', cell: (row) => <Badge status={row.overnight ? 'Active' : 'Inactive'}>{row.overnight ? 'Yes' : 'No'}</Badge> },
    { header: 'Actions', cell: (row) => (
      <div className="flex gap-2">
        <button onClick={() => handleOpenModal(row)} className="p-1.5 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Edit">
          <Edit2 className="w-4 h-4" />
        </button>
        <button onClick={() => { setDeleteId(row.id); setIsDeleteModalOpen(true); }} className="p-1.5 text-danger-500 rounded" title="Delete">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-neutral-900">Shifts</h1>
        <Button onClick={() => handleOpenModal()} className="gap-2">
          <Plus className="w-4 h-4" /> Add Shift
        </Button>
      </div>

      <Table columns={columns} data={shifts} isLoading={loading} />

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Edit Shift' : 'Add Shift'}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          <Input label="Shift Code" {...register('code')} error={errors.code?.message} disabled={!!editingId} />
          <Input label="Shift Name" {...register('name')} error={errors.name?.message} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Start Time" type="time" {...register('startTime')} error={errors.startTime?.message} />
            <Input label="End Time" type="time" {...register('endTime')} error={errors.endTime?.message} />
          </div>
          <Input label="Grace Period (minutes)" type="number" {...register('gracePeriod')} error={errors.gracePeriod?.message} />
          
          <div className="flex items-center gap-2 mt-2">
            <input type="checkbox" id="overnight" className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              {...register('overnight')} 
            />
            <label htmlFor="overnight" className="text-sm text-neutral-700">Overnight Shift</label>
          </div>
          
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button type="submit" isLoading={isSubmitting}>Save</Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Delete Shift">
        <div className="mt-4">
          <p className="text-neutral-600">Are you sure you want to delete this shift? This action cannot be undone.</p>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete}>Delete</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Shifts;
