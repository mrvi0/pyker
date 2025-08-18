import React, { useState } from 'react';
import { ProcessFormData, Script } from '../types';

interface ProcessFormProps {
  scripts: Script[];
  onProcessStart: () => void;
}

export const ProcessForm: React.FC<ProcessFormProps> = ({ scripts, onProcessStart }) => {
  const [formData, setFormData] = useState<ProcessFormData>({
    name: '',
    script_path: '',
    auto_restart: false
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.script_path) {
      alert('Пожалуйста, заполните все поля');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch('/api/processes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setFormData({ name: '', script_path: '', auto_restart: false });
        onProcessStart();
        alert('Процесс успешно запущен!');
      } else {
        const error = await response.json();
        alert(`Ошибка запуска процесса: ${error.detail}`);
      }
    } catch (error) {
      alert('Ошибка соединения с сервером');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">
        Запустить новый процесс
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Название процесса
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="Мой бот"
            required
          />
        </div>

        <div>
          <label htmlFor="script_path" className="block text-sm font-medium text-gray-700">
            Путь к скрипту
          </label>
          <select
            id="script_path"
            value={formData.script_path}
            onChange={(e) => setFormData({ ...formData, script_path: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            required
          >
            <option value="">Выберите скрипт</option>
            {scripts.map((script) => (
              <option key={script.path} value={script.path}>
                {script.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center">
          <input
            id="auto_restart"
            type="checkbox"
            checked={formData.auto_restart}
            onChange={(e) => setFormData({ ...formData, auto_restart: e.target.checked })}
            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
          />
          <label htmlFor="auto_restart" className="ml-2 block text-sm text-gray-900">
            Автоматический перезапуск при ошибке
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {loading ? 'Запуск...' : 'Запустить процесс'}
        </button>
      </form>
    </div>
  );
}; 