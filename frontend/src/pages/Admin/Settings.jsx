import React, { useEffect, useState } from 'react';
import { Save, RotateCcw } from 'lucide-react';
import { api as mockApi } from '../../services/api';
import { useToast } from '../../components/ui/Toast';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Skeleton from '../../components/ui/Skeleton';

const Settings = () => {
  const [settings, setSettings] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState(null);

  const { addToast } = useToast();

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await mockApi.settings.list();
      setSettings(data);
      setDrafts(Object.fromEntries(data.map(item => [item.key, item.value])));
    } catch (err) {
      addToast('Không thể tải cấu hình hệ thống', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async (setting) => {
    setSavingKey(setting.key);
    try {
      await mockApi.settings.update(setting.key, drafts[setting.key]);
      addToast(`Đã cập nhật "${setting.label}"`, 'success');
      loadData();
    } catch (err) {
      addToast(err.message || 'Không thể lưu cấu hình', 'error');
    } finally {
      setSavingKey(null);
    }
  };

  const groups = settings.reduce((acc, item) => {
    (acc[item.group] = acc[item.group] || []).push(item);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-neutral-900">Cấu hình hệ thống</h1>
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">Cấu hình hệ thống</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Các tham số nghiệp vụ có hiệu lực ngay sau khi lưu, không cần khởi động lại hệ thống.
        </p>
      </div>

      {Object.entries(groups).map(([group, items]) => (
        <div key={group} className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-neutral-200 bg-neutral-50">
            <h2 className="font-bold text-neutral-900">{group}</h2>
          </div>
          <div className="divide-y divide-neutral-100">
            {items.map((setting) => {
              const changed = drafts[setting.key] !== setting.value;
              return (
                <div key={setting.key} className="p-6 flex flex-col lg:flex-row lg:items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-neutral-900">{setting.label}</p>
                    <p className="text-sm text-neutral-500 mt-0.5">{setting.description}</p>
                    <p className="text-xs text-neutral-400 mt-1">
                      {setting.key} · cho phép {setting.minimum} – {setting.maximum}
                    </p>
                  </div>
                  <div className="flex items-end gap-2 shrink-0">
                    <Input
                      type="number"
                      step={setting.valueType === 'FLOAT' ? '0.01' : '1'}
                      value={drafts[setting.key] ?? ''}
                      onChange={(e) => setDrafts({ ...drafts, [setting.key]: e.target.value })}
                      className="w-32"
                    />
                    {changed && (
                      <Button
                        variant="ghost"
                        onClick={() => setDrafts({ ...drafts, [setting.key]: setting.value })}
                        title="Hoàn tác"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      onClick={() => handleSave(setting)}
                      disabled={!changed}
                      isLoading={savingKey === setting.key}
                      className="gap-2"
                    >
                      <Save className="w-4 h-4" /> Lưu
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Settings;
