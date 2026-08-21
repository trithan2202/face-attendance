import React, { useEffect, useState } from 'react';
import { CheckCircle, ArrowRightCircle, AlertTriangle, XCircle, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api as mockApi } from '../../services/api';
import Table from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Skeleton from '../../components/ui/Skeleton';

const StatCard = ({ title, value, icon: Icon, colorClass, isLoading }) => (
  <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm flex items-center gap-4">
    <div className={`p-4 rounded-lg ${colorClass} bg-opacity-10`}>
      <Icon className={`w-8 h-8 ${colorClass.split(' ')[0].replace('bg-', 'text-')}`} />
    </div>
    <div>
      <p className="text-sm font-medium text-neutral-500 mb-1">{title}</p>
      {isLoading ? (
        <Skeleton className="h-8 w-16" />
      ) : (
        <h3 className="text-2xl font-bold text-neutral-900">{value}</h3>
      )}
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = useState({ checkIn: 0, checkOut: 0, late: 0, missing: 0 });
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await mockApi.attendance.list({ date: new Date().toISOString().split('T')[0] });
      
      let checkIn = 0, checkOut = 0, late = 0, missing = 0;
      data.forEach(d => {
        if (d.checkInTime) checkIn++;
        if (d.checkOutTime) checkOut++;
        if (d.isLate) late++;
        if (d.status === 'Missing check-out') missing++;
      });
      setStats({ checkIn, checkOut, late, missing });
      
      // Mock recent events based on attendance
      const recent = data.slice(0, 10).map(d => ({
        id: d.id,
        time: d.checkOutTime || d.checkInTime,
        employeeName: d.employeeName,
        employeeCode: d.employeeCode,
        department: d.department,
        type: d.checkOutTime ? 'Check-out' : 'Check-in',
        status: 'Thành công'
      }));
      setEvents(recent);
    } catch (err) {
      setError('Không thể tải dữ liệu tổng quan. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const columns = [
    { header: 'Thời gian', accessorKey: 'time' },
    { header: 'Nhân viên', cell: (row) => (
      <div>
        <div className="font-medium text-neutral-900">{row.employeeName}</div>
        <div className="text-xs text-neutral-500">{row.employeeCode}</div>
      </div>
    )},
    { header: 'Phòng ban', cell: (row) => row.department || '—' },
    { header: 'Loại sự kiện', accessorKey: 'type' },
    { header: 'Trạng thái', cell: (row) => (
      <Badge status={row.status === 'Thành công' ? 'Active' : 'Absent'}>
        {row.status}
      </Badge>
    )}
  ];

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className="text-danger-500 mb-4">{error}</p>
        <button onClick={loadData} className="text-primary-600 font-medium hover:underline">Thử lại</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-neutral-900">Tổng quan</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Check-in hôm nay" value={stats.checkIn} icon={CheckCircle} colorClass="bg-success-500 text-success-500" isLoading={loading} />
        <StatCard title="Check-out hôm nay" value={stats.checkOut} icon={ArrowRightCircle} colorClass="bg-primary-500 text-primary-500" isLoading={loading} />
        <StatCard title="Đi trễ" value={stats.late} icon={AlertTriangle} colorClass="bg-warning-500 text-warning-500" isLoading={loading} />
        <StatCard title="Thiếu Check-out" value={stats.missing} icon={XCircle} colorClass="bg-danger-500 text-danger-500" isLoading={loading} />
      </div>

      <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-neutral-200 flex justify-between items-center bg-white">
          <h2 className="text-lg font-bold text-neutral-900">Sự kiện gần đây</h2>
          <Link to="/admin/attendance" className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1">
            Xem tất cả <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
        <Table columns={columns} data={events} isLoading={loading} className="border-0 rounded-none shadow-none" />
      </div>
    </div>
  );
};

export default Dashboard;
