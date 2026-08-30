import React from "react";
import { X } from "lucide-react";
import { Link } from "react-router-dom";

interface PdfViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string;
  title?: string;
  showCorrectionsLink?: boolean;
}

const PdfViewerModal: React.FC<PdfViewerModalProps> = ({
  isOpen,
  onClose,
  pdfUrl,
  title = "Document Preview",
  showCorrectionsLink = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full h-[90vh] max-w-6xl flex flex-col shadow-2xl">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="font-bold text-lg">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close preview"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 bg-gray-100 p-2 overflow-auto">
          {/* Convert Cloudinary PDF to images */}
          <div className="flex flex-col items-center gap-4 p-4">
            {/* This will show the first page as an image */}
            <img
              src={pdfUrl.replace("/upload/", "/upload/pg_1,f_jpg/")}
              alt="PDF Page 1"
              className="shadow-lg max-w-full"
            />
            {/* You can add more pages by changing pg_1 to pg_2, pg_3, etc. */}
          </div>
        </div>

        <div className="p-3 border-t bg-gray-50 flex justify-end gap-3">
          {/* <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline text-sm font-medium"
          >
            Open in New Tab
          </a> */}
          {showCorrectionsLink && (
            <Link
              to="/feedback-page"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-600 hover:underline text-sm font-medium"
            >
              MAKE CORRECTIONS
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default PdfViewerModal;
