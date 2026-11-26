import { useState, useEffect } from 'react';
import { Calendar, Store as StoreIcon, Package, Camera, Trash2, Eye, Filter } from 'lucide-react';
import { Link } from 'react-router-dom';
import { storesApi, productsApi, scansApi } from '../services/api';
import type { Store, Product, ScanList, Scan } from '../types';

const Scans = () => {
  const [scans, setScans] = useState<ScanList[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filter states
  const [filters, setFilters] = useState({
    store_id: '',
    product_id: '',
    start_date: '',
    end_date: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchScans();
  }, [filters]);

  const fetchData = async () => {
    try {
      const [storesRes, productsRes] = await Promise.all([
        storesApi.getAll(),
        productsApi.getAll()
      ]);
      setStores(storesRes.data);
      setProducts(productsRes.data);
    } catch {
      setError('Failed to fetch data');
    }
  };

  const fetchScans = async () => {
    try {
      const params = {
        ...(filters.store_id && { store_id: Number(filters.store_id) }),
        ...(filters.product_id && { product_id: Number(filters.product_id) }),
        ...(filters.start_date && { start_date: filters.start_date }),
        ...(filters.end_date && { end_date: filters.end_date })
      };
      
      const response = await scansApi.getAll(params);
      setScans(response.data);
    } catch {
      setError('Failed to fetch scans');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      store_id: '',
      product_id: '',
      start_date: '',
      end_date: ''
    });
  };

  const openDetailModal = async (scan: ScanList) => {
    try {
      const response = await scansApi.getById(scan.id);
      setSelectedScan(response.data);
      setShowDetailModal(true);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch scan details');
    }
  };

  const openDeleteModal = (scan: ScanList) => {
    setSelectedScan(scan as unknown as Scan);
    setShowDeleteModal(true);
    setError('');
  };

  const handleDelete = async () => {
    if (!selectedScan) return;

    try {
      await scansApi.delete(selectedScan.id);
      setSuccess('Scan deleted successfully');
      setShowDeleteModal(false);
      setSelectedScan(null);
      fetchScans();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete scan');
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Scans</h1>
          <p className="text-gray-600">Manage and view scan history</p>
        </div>
        <Link
          to="/upload"
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <Camera className="h-4 w-4 mr-2" />
          New Scan
        </Link>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md">
          {success}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            Filters
          </h3>
          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear all
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Store
            </label>
            <select
              value={filters.store_id}
              onChange={(e) => handleFilterChange('store_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Stores</option>
              {stores.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Product
            </label>
            <select
              value={filters.product_id}
              onChange={(e) => handleFilterChange('product_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Products</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Scans List */}
      <div className="bg-white shadow rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Store
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Count
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {scans.map((scan) => (
                <tr key={scan.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <StoreIcon className="h-5 w-5 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">{scan.store_name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Package className="h-5 w-5 text-gray-400 mr-2" />
                      <span className="text-sm text-gray-900">{scan.product_name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {scan.count} items
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ width: `${scan.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-900">{(scan.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-500">
                      <Calendar className="h-4 w-4 mr-1" />
                      {new Date(scan.scanned_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => openDetailModal(scan)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => openDeleteModal(scan)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {scans.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Camera className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No scans found</h3>
              <p className="text-sm text-gray-500 mb-4">
                {Object.values(filters).some(v => v) 
                  ? 'Try adjusting your filters' 
                  : 'Get started by uploading your first scan'
                }
              </p>
              {!Object.values(filters).some(v => v) && (
                <Link
                  to="/upload"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <Camera className="h-4 w-4 mr-2" />
                  Upload Scan
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedScan && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">Scan Details</h3>
              <button
                onClick={() => setShowDetailModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Scan Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Store</h4>
                  <p className="text-gray-900">{selectedScan.store?.name}</p>
                  <p className="text-sm text-gray-500">{selectedScan.store?.location}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Product</h4>
                  <p className="text-gray-900">{selectedScan.product?.name}</p>
                  <p className="text-sm text-gray-500">SKU: {selectedScan.product?.sku || 'N/A'}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Analysis Results</h4>
                  <p className="text-gray-900">Count: {selectedScan.count}</p>
                  <p className="text-gray-900">Confidence: {(selectedScan.confidence * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Scan Date</h4>
                  <p className="text-gray-900">{new Date(selectedScan.scanned_at).toLocaleString()}</p>
                  {selectedScan.notes && <p className="text-sm text-gray-500 mt-1">Notes: {selectedScan.notes}</p>}
                </div>
              </div>

              {/* Image */}
              {selectedScan.image_path && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Scanned Image</h4>
                  <img 
                    src={`http://localhost:8000/${selectedScan.image_path}`}
                    alt="Scanned" 
                    className="w-full h-auto max-h-96 object-contain rounded-md border"
                  />
                </div>
              )}

              {/* Detections */}
              {selectedScan.detections && selectedScan.detections.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Detections ({selectedScan.detections.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {selectedScan.detections.map((detection) => (
                      <div key={detection.id} className="border rounded-md p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{detection.label}</p>
                            <p className="text-sm text-gray-500">
                              Confidence: {(detection.confidence * 100).toFixed(1)}%
                            </p>
                          </div>
                          {detection.area && (
                            <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                              {detection.area.toFixed(3)}
                            </span>
                          )}
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                          <p>Box: ({detection.x1.toFixed(2)}, {detection.y1.toFixed(2)}) - ({detection.x2.toFixed(2)}, {detection.y2.toFixed(2)})</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Segmentation Masks */}
              {selectedScan.segmentation_masks && selectedScan.segmentation_masks.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Segmentation Masks ({selectedScan.segmentation_masks.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedScan.segmentation_masks.map((mask) => (
                      <div key={mask.id} className="border rounded-md p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{mask.label}</p>
                            <p className="text-sm text-gray-500">Type: {mask.mask_type}</p>
                            {mask.confidence && (
                              <p className="text-sm text-gray-500">
                                Confidence: {(mask.confidence * 100).toFixed(1)}%
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedScan && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <Trash2 className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Scan</h3>
              <p className="text-sm text-gray-500 mb-4">
                Are you sure you want to delete this scan from {selectedScan.store?.name} for {selectedScan.product?.name}? This action cannot be undone.
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

export default Scans;
