import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import { User, Lock, AlertCircle, Eye, EyeOff } from 'lucide-react';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

const Login = () => {
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(loginSchema)
  });

  const onSubmit = async (data) => {
    try {
      setError('');
      await login(data.username, data.password);
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-card p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
             <span className="text-3xl font-bold text-primary-600">FA</span>
          </div>
          <h1 className="text-2xl font-bold text-neutral-900">Attendance System</h1>
          <p className="text-neutral-500 mt-2 text-sm">Sign in to admin dashboard</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-md flex items-start gap-3 text-danger-700">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <Input
            label="Username"
            placeholder="Enter your username"
            icon={User}
            error={errors.username?.message}
            {...register('username')}
          />
          
          <div className="relative">
            <Input
              type={showPassword ? 'text' : 'password'}
              label="Password"
              placeholder="Enter your password"
              icon={Lock}
              error={errors.password?.message}
              {...register('password')}
            />
            <button
              type="button"
              className="absolute right-3 top-[34px] text-neutral-400 hover:text-neutral-600"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
            Sign In
          </Button>
        </form>
      </div>
    </div>
  );
};

export default Login;
