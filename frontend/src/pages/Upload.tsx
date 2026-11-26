import { useState, useEffect } from 'react';
import { Upload, Camera, AlertCircle } from 'lucide-react';
import { storesApi, productsApi, scansApi } from '../services/api';
import type { Store, Product, Scan } from '../types';

const UploadPage = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedStore, setSelectedStore] = useState<number | ''>('');
  const [selectedProduct, setSelectedProduct] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string>('');
  const [result, setResult] = useState<Scan | null>(null);
  const [error, setError] = useState<string>('');
  const [showAnnotated, setShowAnnotated] = useState(false);
  const [annotatedImage, setAnnotatedImage] = useState<string>('');
  const [loadingAnnotated, setLoadingAnnotated] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [storesRes, productsRes] = await Promise.all([
          storesApi.getAll(),
          productsApi.getAll()
        ]);
        setStores(storesRes.data);
        setProducts(productsRes.data);
      } catch {
        setError('Failed to load stores and products');
      }
    };
    fetchData();
  }, []);

  const loadAnnotatedImage = async (scanId: number) => {
    if (loadingAnnotated) return;
    setLoadingAnnotated(true);
    try {
      const response = await scansApi.getAnnotated(scanId, {
        style: 'pil',
        show_confidence: true,
        show_labels: true
      });
      const annotatedPath = response.data.annotated_image_path;
      setAnnotatedImage(`http://localhost:8000/${annotatedPath}`);
      setShowAnnotated(true);
    } catch {
      setError('Failed to load annotated image');
    } finally {
      setLoadingAnnotated(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !selectedStore || !selectedProduct) {
      setError('Please select a file, store, and product');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('store_id', selectedStore.toString());
      formData.append('product_id', selectedProduct.toString());
      if (notes) formData.append('notes', notes);

      const response = await scansApi.create(formData);
      setResult(response.data);
      setShowAnnotated(false);
      setAnnotatedImage('');
      
      // Clear form
      setSelectedFile(null);
      setSelectedStore('');
      setSelectedProduct('');
      setNotes('');
      setPreview('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-4">
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Upload Shelf Photo</h3>
          <p className="mt-1 text-sm text-gray-500">Inventory analysis with AI-powered detection</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Shelf Photo</label>
            <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
              <div className="space-y-1 text-center">
                {preview ? (
                  <div className="space-y-4">
                    <img src={preview} alt="Preview" className="mx-auto h-64 w-auto object-cover rounded-md" />
                    <button type="button" onClick={() => {setPreview(''); setSelectedFile(null);}} className="text-sm text-red-600">Remove</button>
                  </div>
                ) : (
                  <>
                    <Camera className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label htmlFor="file-input" className="cursor-pointer text-blue-600 hover:text-blue-500 font-medium">
                        <span>Upload a file</span>
                        <input id="file-input" type="file" className="sr-only" accept="image/*" onChange={handleFileChange} />
                      </label>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <select value={selectedStore} onChange={(e) => setSelectedStore(Number(e.target.value))} className="w-full p-2 border rounded-md" required>
              <option value="">Select a store</option>
              {stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(Number(e.target.value))} className="w-full p-2 border rounded-md" required>
              <option value="">Select a product</option>
              {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>

          {error && <div className="p-4 bg-red-50 text-red-800 rounded-md flex items-center"><AlertCircle className="mr-2 h-5 w-5"/>{error}</div>}

          <div className="flex justify-end">
            <button type="submit" disabled={uploading} className="px-6 py-2 bg-blue-600 text-white rounded-md flex items-center disabled:opacity-50">
              {uploading ? "Analyzing..." : <><Upload className="mr-2 h-4 w-4"/> Upload & Analyze</>}
            </button>
          </div>
        </form>
      </div>

      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-3 gap-4 mb-6 text-center">
            <div><div className="text-2xl font-bold text-blue-600">{result.count}</div><div className="text-xs text-gray-500">Detected</div></div>
            <div><div className="text-2xl font-bold text-green-600">{(result.confidence * 100).toFixed(1)}%</div><div className="text-xs text-gray-500">Confidence</div></div>
            <div><div className="text-2xl font-bold text-purple-600">{result.detections?.length || 0}</div><div className="text-xs text-gray-500">Boxes</div></div>
          </div>
          <div className="relative">
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-sm font-bold">Analysis View</h4>
              <button onClick={() => showAnnotated ? setShowAnnotated(false) : loadAnnotatedImage(result.id)} className="text-xs bg-gray-100 px-2 py-1 rounded">
                {showAnnotated ? 'Hide Boxes' : 'Show Boxes'}
              </button>
            </div>
            <img 
              src={showAnnotated && annotatedImage ? annotatedImage : `http://localhost:8000/${result.image_path}`} 
              className="w-full h-auto rounded-md" 
              alt="Scan" 
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;