import { useState } from "react";
import { Save, X } from "lucide-react";

interface ConfigKey {
  key: string;
  label: string;
  value: string;
  field_type: "STRING" | "PASSWORD" | "BOOLEAN" | "INTEGER";
  help_text?: string;
  is_required: boolean;
}

interface Integration {
  identifier: string;
  name: string;
  config_keys: ConfigKey[];
}

interface ConfigFormProps {
  integration: Integration;
  onSave: (identifier: string, data: Record<string, any>) => void;
  onCancel: () => void;
  isSaving: boolean;
}

export default function ConfigForm({ integration, onSave, onCancel, isSaving }: ConfigFormProps) {
  // Initialize state with existing values
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    integration.config_keys.forEach((k) => {
        // Boolean fields need real booleans, others are strings
        initial[k.key] = k.field_type === 'BOOLEAN' ? (k.value === 'true') : (k.value || '');
    });
    return initial;
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(integration.identifier, formData);
  };

  return (
    <div className="bg-gray-50 border-t border-gray-100 p-6 rounded-b-xl animate-in slide-in-from-top-2">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-4">
          {integration.config_keys.map((field) => (
            <div key={field.key} className="space-y-1.5">
              <div className="flex justify-between">
                <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                  {field.label} {field.is_required && <span className="text-red-500">*</span>}
                </label>
              </div>

              {/* DYNAMIC FIELD RENDERING */}
              {field.field_type === "BOOLEAN" ? (
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, [field.key]: !prev[field.key] }))}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            formData[field.key] ? "bg-indigo-600" : "bg-gray-200"
                        }`}
                    >
                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            formData[field.key] ? "translate-x-6" : "translate-x-1"
                        }`} />
                    </button>
                    <span className="text-sm text-gray-500">{formData[field.key] ? "Enabled" : "Disabled"}</span>
                </div>
              ) : field.field_type === "PASSWORD" ? (
                <div className="relative">
                  <input
                    type="password"
                    value={formData[field.key]}
                    onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                    placeholder={field.value ? "******** (Unchanged)" : "Enter secret..."}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  />
                  {field.value && !formData[field.key] && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-green-600 font-medium flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span> Configured
                    </div>
                  )}
                </div>
              ) : (
                <input
                  type="text"
                  value={formData[field.key]}
                  onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              )}

              {field.help_text && (
                <p className="text-xs text-gray-400">{field.help_text}</p>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 mt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-all disabled:opacity-70"
          >
            {isSaving ? "Saving..." : <><Save size={16} /> Save Changes</>}
          </button>
        </div>
      </form>
    </div>
  );
}