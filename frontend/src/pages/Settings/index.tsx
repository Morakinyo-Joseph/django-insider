import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSettings, updateSetting  } from "../../api/client";
import { Save, ToggleLeft, ToggleRight } from "lucide-react";
import type { InsiderSetting } from "../../types";

export default function Settings() {
  const queryClient = useQueryClient();
  
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  const mutation = useMutation({
    mutationFn: ({ id, value }: { id: number; value: any }) => updateSetting(id, value),
    onSuccess: () => {
      // Refresh data to ensure sync
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading configurations...</div>;
  if (error) return <div className="p-8 text-red-600">Failed to load settings.</div>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm">
           Manage the behavior of the Insider package. Changes apply immediately.
        </p>
      </div>

      <div className="grid gap-4">
        {settings?.map((setting) => (
          <SettingCard 
            key={setting.id} 
            setting={setting} 
            onSave={(val) => mutation.mutate({ id: setting.id, value: val })}
            isSaving={mutation.isPending && mutation.variables?.id === setting.id}
          />
        ))}
      </div>
    </div>
  );
}

// --- DYNAMIC CARD COMPONENT ---
function SettingCard({ setting, onSave, isSaving }: { 
  setting: InsiderSetting; 
  onSave: (val: any) => void;
  isSaving: boolean; 
}) {
  // Local state for inputs (text/number) to prevent jitter while typing
  const [localValue, setLocalValue] = useState(setting.value);
  const [isDirty, setIsDirty] = useState(false);

  // Update local state if remote setting changes (and we aren't editing)
  useEffect(() => {
     if (!isDirty) setLocalValue(setting.value);
  }, [setting.value, isDirty]);

  // Handler for saving
  const handleSave = () => {
    let finalValue = localValue;

    // Data Transformation for Lists (String -> Array)
    if (setting.field_type === 'LIST' && typeof localValue === 'string') {
       finalValue = localValue.split(',').map((s: string) => s.trim()).filter((s: string) => s !== "");
    }

    onSave(finalValue);
    setIsDirty(false);
  };

  return (
    <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      
      {/* LEFT: Label & Description */}
      <div className="flex-1">
        <div className="flex items-center gap-2">
           <h3 className="font-bold text-gray-800 text-sm font-mono">{setting.key}</h3>
           {isDirty && <span className="text-[10px] text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full font-medium">Unsaved</span>}
        </div>
        <p className="text-gray-500 text-xs mt-1">{setting.description}</p>
      </div>

      {/* RIGHT: Dynamic Input */}
      <div className="sm:w-1/2 flex items-center justify-end gap-3">
        
        {/* BOOLEAN: Toggle Switch */}
        {setting.field_type === 'BOOLEAN' && (
          <button 
            onClick={() => onSave(!setting.value)} // Auto-save on toggle
            className={`transition-colors ${setting.value ? 'text-indigo-600' : 'text-gray-300'}`}
          >
            {setting.value ? <ToggleRight size={32} /> : <ToggleLeft size={32} />}
          </button>
        )}

        {/* INTEGER: Number Input */}
        {setting.field_type === 'INTEGER' && (
          <div className="flex gap-2 w-full">
            <input 
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
              value={localValue || ''}
              onChange={(e) => {
                 setLocalValue(e.target.value === '' ? null : parseInt(e.target.value));
                 setIsDirty(true);
              }}
            />
          </div>
        )}

        {/* STRING: Text Input */}
        {setting.field_type === 'STRING' && (
          <div className="flex gap-2 w-full">
            <input 
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
              value={localValue || ''}
              onChange={(e) => {
                 setLocalValue(e.target.value);
                 setIsDirty(true);
              }}
            />
          </div>
        )}

        {/* LIST: Text Input (Comma Separated) */}
        {setting.field_type === 'LIST' && (
          <div className="flex flex-col w-full gap-1">
            <input 
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
              // If it's an array, join it for display. If it's already a string (user typing), keep it.
              value={Array.isArray(localValue) ? localValue.join(', ') : localValue}
              onChange={(e) => {
                 setLocalValue(e.target.value);
                 setIsDirty(true);
              }}
              placeholder="item1, item2"
            />
            <span className="text-[10px] text-gray-400 text-right italic">Comma separated</span>
          </div>
        )}

        {/* SAVE BUTTON (Only for non-booleans) */}
        {setting.field_type !== 'BOOLEAN' && (
          <button 
             onClick={handleSave}
             disabled={!isDirty || isSaving}
             className={`p-2 rounded-lg transition-all ${
               isDirty 
                 ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md" 
                 : "bg-gray-100 text-gray-300 cursor-not-allowed"
             }`}
          >
            {isSaving ? <span className="animate-spin">⟳</span> : <Save size={18} />}
          </button>
        )}
      </div>
    </div>
  );
}