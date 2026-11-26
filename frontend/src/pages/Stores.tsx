import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Store as StoreIcon, MapPin, FileText } from 'lucide-react';
import { storesApi } from '../services/api';
import type { Store, StoreCreate } from '../types';
import { useToast } from '../hooks/useToast';

const Stores = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [formData, setFormData] = useState<StoreCreate>({
    name: '',
    location: '',
    description: ''
  });
  const { addToast } = useToast();

  useEffect(() => {
    fetchStores();
  }, []);

  const fetchStores = async () => {
    try {
      const response = await storesApi.getAll();
      setStores(response.data);
    } catch {
      addToast('Failed to fetch stores', 'error');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      location: '',
      description: ''
    });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      addToast('Store name is required', 'error');
      return;
    }

    try {
      await storesApi.create(formData);
      addToast('Store created successfully', 'success');
      setShowCreateModal(false);
      resetForm();
      fetchStores();
    } catch (err: any) {
      addToast(err.response?.data?.detail || 'Failed to create store', 'error');
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      addToast('Store name is required', 'error');
      return;
    }

    if (!selectedStore) return;

    try {
      await storesApi.update(selectedStore.id, formData);
      addToast('Store updated successfully', 'success');
      setShowEditModal(false);
      setSelectedStore(null);
      resetForm();
      fetchStores();
    } catch (err: any) {
      addToast(err.response?.data?.detail || 'Failed to update store', 'error');
    }
  };

  const handleDelete = async () => {
    if (!selectedStore) return;

    try {
      await storesApi.delete(selectedStore.id);
      addToast('Store deleted successfully', 'success');
      setShowDeleteModal(false);
      setSelectedStore(null);
      fetchStores();
    } catch (err: any) {
      addToast(err.response?.data?.detail || 'Failed to delete store', 'error');
    }
  };

  const openEditModal = (store: Store) => {
    setSelectedStore(store);
    setFormData({
      name: store.name,
      location: store.location || '',
      description: store.description || ''
    });
    setShowEditModal(true);
  };

  const openDeleteModal = (store: Store) => {
    setSelectedStore(store);
    setShowDeleteModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Stores</h1>
          <p className="text-gray-600">Manage your store locations</p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowCreateModal(true);
          }}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Store
        </button>
      </div>

      {/* Success/Error Messages - Removed in favor of toast notifications */}

      {/* Stores List */}
      <div className="bg-white shadow rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Store Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stores.map((store) => (
                <tr key={store.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <StoreIcon className="h-5 w-5 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">{store.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-500">
                      <MapPin className="h-4 w-4 mr-1" />
                      {store.location || 'No location'}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-start text-sm text-gray-500">
                      <FileText className="h-4 w-4 mr-1 mt-0.5" />
                      <span className="line-clamp-2">{store.description || 'No description'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(store.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => openEditModal(store)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => openDeleteModal(store)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {stores.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <StoreIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No stores</h3>
              <p className="text-sm text-gray-500 mb-4">Get started by adding your first store</p>
              <button
                onClick={() => {
                  resetForm();
                  setShowCreateModal(true);
                }}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Store
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add New Store</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Store Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Create Store
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Edit Store</h3>
            <form onSubmit={handleEdit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Store Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Update Store
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <Trash2 className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Store</h3>
              <p className="text-sm text-gray-500 mb-4">
                Are you sure you want to delete "{selectedStore?.name}"? This action cannot be undone.
              </p>
              <div className="flex justify-center space-x-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Stores;
