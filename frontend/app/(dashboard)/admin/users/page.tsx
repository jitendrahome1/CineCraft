/**
 * User management page for admins.
 */
'use client';

import { useEffect, useState } from 'react';
import { apiClient, type User } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button, Spinner } from '@/components/ui';
import { Shield, Ban, CheckCircle2, Mail } from 'lucide-react';
import { format } from 'date-fns';

export default function UsersManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await apiClient.get<{ items: User[] }>('/api/v1/admin/users?skip=0&limit=100');
      setUsers(response.items);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleAdmin = async (userId: number, isAdmin: boolean) => {
    try {
      await apiClient.patch(`/api/v1/admin/users/${userId}`, {
        is_admin: !isAdmin,
      });
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update user');
    }
  };

  const handleToggleActive = async (userId: number, isActive: boolean) => {
    try {
      if (isActive) {
        await apiClient.post(`/api/v1/admin/users/${userId}/ban`);
      } else {
        await apiClient.post(`/api/v1/admin/users/${userId}/unban`);
      }
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update user');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
        <p className="mt-2 text-gray-600">
          Manage user accounts and permissions
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>All Users ({users.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {users.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-medium text-gray-900">
                      {user.full_name || 'Unnamed User'}
                    </h3>
                    {user.is_admin && (
                      <Badge variant="info">
                        <Shield className="h-3 w-3 mr-1" />
                        Admin
                      </Badge>
                    )}
                    {!user.is_active && (
                      <Badge variant="danger">
                        <Ban className="h-3 w-3 mr-1" />
                        Banned
                      </Badge>
                    )}
                    {user.is_active && (
                      <Badge variant="success">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <Mail className="h-4 w-4" />
                      {user.email}
                    </span>
                    <span>
                      ID: {user.id}
                    </span>
                    <span>
                      Joined {format(new Date(user.created_at), 'MMM d, yyyy')}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant={user.is_admin ? 'outline' : 'secondary'}
                    onClick={() => handleToggleAdmin(user.id, user.is_admin)}
                  >
                    {user.is_admin ? 'Remove Admin' : 'Make Admin'}
                  </Button>
                  <Button
                    size="sm"
                    variant={user.is_active ? 'danger' : 'secondary'}
                    onClick={() => handleToggleActive(user.id, user.is_active)}
                  >
                    {user.is_active ? 'Ban User' : 'Unban User'}
                  </Button>
                </div>
              </div>
            ))}

            {users.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-600">No users found</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
