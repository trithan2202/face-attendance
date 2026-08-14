import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Download, Edit2, History, Search } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Table from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Modal from '../../components/ui/Modal';
import Skeleton from '../../components/ui/Skeleton';

const updateSchema = z.object({
  checkInTime: z.string().optional(),
  checkOutTime: z.string().optional(),
  status: z.string().min(1, 'Status is required'),
  reason: z.string().min(1, 'Reason is required'),
});

const Attendance = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [filterDate, setFilterDate] = useState(new Date().toISOString().split('T')[0]);
  const [reportMonth, setReportMonth] = useState(new Date().toISOString().slice(0, 7));
  const [filterStatus, setFilterStatus] = useState('All');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const { addToast } = useToast();

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(updateSchema)
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await mockApi.attendance.list({ date: filterDate, status: filterStatus });
      setRecords(data);
    } catch (err) {
      addToast('Failed to load attendance records', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterDate, filterStatus]);

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
      addToast('Record updated successfully', 'success');
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      addToast('Operation failed', 'error');
    }
  };

  const handleOpenAudit = async (id) => {
    setIsAuditModalOpen(true);
    setAuditLoading(true);
    try {
      const logs = await mockApi.attendance.getAudit(id);
      setAuditLogs(logs);
    } catch (err) {
      addToast('Failed to load audit logs', 'error');
    } finally {
      setAuditLoading(false);
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
      const blob = await mockApi.attendance.exportExcel({ date: filterDate, status: filterStatus });
      downloadBlob(blob, `attendance_${filterDate}.xlsx`);
    } catch (err) {
      addToast('Xuất Excel theo ngày thất bại', 'error');
    }
  };

  const handleMonthlyExport = async () => {
    if (!reportMonth) {
      addToast('Hãy chọn tháng cần xuất báo cáo', 'error');
      return;
    }
    try {
      const blob = await mockApi.attendance.exportMonthlyExcel({ month: reportMonth });
      downloadBlob(blob, `attendance_monthly_${reportMonth}.xlsx`);
    } catch (err) {
      addToast('Xuất báo cáo tháng thất bại', 'error');
    }
  };

  const columns = [
    { header: 'Employee', cell: (row) => (
        <div>
            <div className="font-medium text-neutral-900">{row.employeeName}</div>
            <div className="text-xs text-neutral-500">{row.employeeCode}</div>
        </div>
    )},
    { header: 'Department', accessorKey: 'department' },
    { header: 'Shift', accessorKey: 'shift' },
    { header: 'Check-in', accessorKey: 'checkInTime' },
    { header: 'Check-out', accessorKey: 'checkOutTime' },
    { header: 'Status', cell: (row) => <Badge status={row.status}>{row.status}</Badge> },
    { header: 'Actions', cell: (row) => (
      <div className="flex gap-2">
        <button onClick={() => handleOpenEdit(row)} className="p-1.5 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded" title="Edit Record">
          <Edit2 className="w-4 h-4" />
        </button>
        <button onClick={() => handleOpenAudit(row.id)} className="p-1.5 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 rounded" title="View Audit Trail">
          <History className="w-4 h-4" />
        </button>
      </div>
    )}
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-neutral-900">Attendance</h1>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleDailyExport} variant="secondary" className="gap-2">
            <Download className="w-4 h-4" /> Xuất Excel ngày
          </Button>
          <Button onClick={handleMonthlyExport} variant="secondary" className="gap-2">
            <Download className="w-4 h-4" /> Báo cáo tháng
          </Button>
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-sm flex flex-col sm:flex-row gap-4 items-end">
        <Input 
          label="Date"
          type="date"
          value={filterDate}
          onChange={(e) => setFilterDate(e.target.value)}
          className="max-w-[200px]"
        />
        <Select 
          label="Status"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          options={[
            { value: 'All', label: 'All Statuses' },
            { value: 'Present', label: 'Present' },
            { value: 'Missing check-in', label: 'Missing check-in' },
            { value: 'Missing check-out', label: 'Missing check-out' },
            { value: 'Absent', label: 'Absent' },
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
        <Button variant="primary" onClick={loadData} className="mb-[2px]">Filter</Button>
      </div>

      <Table columns={columns} data={records} isLoading={loading} emptyMessage="No attendance records found for this date." />

      {/* Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Edit Attendance Record">
        {editingRecord && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
            <div className="bg-neutral-50 p-3 rounded-md mb-4 border border-neutral-200">
              <p className="text-sm font-medium">Employee: {editingRecord.employeeName}</p>
              <p className="text-sm text-neutral-500">Date: {editingRecord.date}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <Input label="Check-in Time" type="time" {...register('checkInTime')} error={errors.checkInTime?.message} />
              <Input label="Check-out Time" type="time" {...register('checkOutTime')} error={errors.checkOutTime?.message} />
            </div>
            
            <Select 
              label="Status" 
              {...register('status')} 
              error={errors.status?.message}
              options={[
                { value: 'Present', label: 'Present' },
                { value: 'Absent', label: 'Absent' },
                { value: 'Missing check-in', label: 'Missing check-in' },
                { value: 'Missing check-out', label: 'Missing check-out' },
              ]}
            />
            
            <div className="flex flex-col gap-1 w-full">
               <label className="text-sm font-medium text-neutral-700">Reason for Edit <span className="text-danger-500">*</span></label>
               <textarea 
                  className={`w-full rounded-md border bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 ${errors.reason ? 'border-danger-500 focus:ring-danger-500' : 'border-neutral-300'}`}
                  rows="3"
                  placeholder="Enter reason for this manual change"
                  {...register('reason')}
               />
               {errors.reason && <span className="text-xs text-danger-500">{errors.reason.message}</span>}
            </div>
            
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
              <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
              <Button type="submit" isLoading={isSubmitting}>Save Changes</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Audit Modal */}
      <Modal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        title="Audit Trail"
        panelClassName="max-w-[548px]"
      >
        <div className="mt-4 max-h-96 overflow-y-auto">
          {auditLoading ? (
            <div className="space-y-4">
              {[1, 2].map(i => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : auditLogs.length === 0 ? (
            <p className="text-neutral-500 text-sm text-center py-4">No edits have been made to this record.</p>
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
                        <div className="text-sm text-neutral-500 mb-2">Reason: <span className="font-medium text-neutral-700">{log.reason}</span></div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-danger-50 p-2 rounded text-danger-700 border border-danger-100">
                            <span className="block font-semibold mb-1">Old Value:</span>
                            {Object.entries(log.oldValue).map(([k, v]) => (
                               v && k !== 'id' && k !== 'employeeId' ? <div key={k}>{k}: {v}</div> : null
                            ))}
                          </div>
                          <div className="bg-success-50 p-2 rounded text-success-700 border border-success-100">
                            <span className="block font-semibold mb-1">New Value:</span>
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
