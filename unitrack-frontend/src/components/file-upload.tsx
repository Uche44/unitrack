import { FileText, X } from "lucide-react";

interface FileUploadProps {
  file?: File | null;
  onFileSelect: (file: File | null) => void;
  label?: string;
}

export const FileUpload = ({
  file,
  onFileSelect,
  label = "Click to upload proposal",
}: FileUploadProps) => {
  return (
    <div className="border-2 border-dashed border-green-500 rounded-lg p-4 text-center">
      {!file ? (
        <>
          <input
            type="file"
            id="fileInput"
            className="hidden"
            onChange={(e) => onFileSelect(e.target.files?.[0] || null)}
          />
          <label
            htmlFor="fileInput"
            className="cursor-pointer text-green-700 font-semibold"
          >
            {label}
          </label>
        </>
      ) : (
        <div className="flex items-center justify-between bg-green-50 p-3 rounded-md">
          <div className="flex items-center gap-2">
            <FileText className="text-green-700" />
            <div className="text-left">
              <p className="text-sm font-semibold">{file.name}</p>
              <p className="text-xs text-gray-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onFileSelect(null)}
            className="text-red-500 hover:text-red-700"
          >
            <X />
          </button>
        </div>
      )}
    </div>
  );
};
