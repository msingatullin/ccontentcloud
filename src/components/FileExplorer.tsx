import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Folder, 
  FolderOpen, 
  FileText, 
  FileCode, 
  Image, 
  Plus,
  ChevronRight,
  ChevronDown
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  isOpen?: boolean;
}

const initialFiles: FileNode[] = [
  {
    id: '1',
    name: 'src',
    type: 'folder',
    isOpen: true,
    children: [
      {
        id: '2',
        name: 'components',
        type: 'folder',
        isOpen: true,
        children: [
          { id: '3', name: 'App.tsx', type: 'file' },
          { id: '4', name: 'Header.tsx', type: 'file' },
          { id: '5', name: 'ChatSidebar.tsx', type: 'file' },
        ],
      },
      { id: '6', name: 'index.css', type: 'file' },
      { id: '7', name: 'main.tsx', type: 'file' },
    ],
  },
  {
    id: '8',
    name: 'public',
    type: 'folder',
    children: [
      { id: '9', name: 'favicon.ico', type: 'file' },
      { id: '10', name: 'logo.png', type: 'file' },
    ],
  },
  { id: '11', name: 'package.json', type: 'file' },
  { id: '12', name: 'tailwind.config.ts', type: 'file' },
];

export const FileExplorer = () => {
  const [files, setFiles] = useState<FileNode[]>(initialFiles);
  const [selectedFile, setSelectedFile] = useState<string>('3');

  const toggleFolder = (id: string) => {
    const updateNode = (nodes: FileNode[]): FileNode[] => {
      return nodes.map(node => {
        if (node.id === id && node.type === 'folder') {
          return { ...node, isOpen: !node.isOpen };
        }
        if (node.children) {
          return { ...node, children: updateNode(node.children) };
        }
        return node;
      });
    };
    setFiles(updateNode(files));
  };

  const getFileIcon = (fileName: string, type: 'file' | 'folder', isOpen?: boolean) => {
    if (type === 'folder') {
      return isOpen ? FolderOpen : Folder;
    }
    
    const ext = fileName.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'tsx':
      case 'ts':
      case 'js':
      case 'jsx':
        return FileCode;
      case 'png':
      case 'jpg':
      case 'svg':
        return Image;
      default:
        return FileText;
    }
  };

  const renderFileNode = (node: FileNode, depth = 0) => {
    const Icon = getFileIcon(node.name, node.type, node.isOpen);
    const isSelected = selectedFile === node.id;

    return (
      <div key={node.id}>
        <div
          className={cn(
            "flex items-center gap-2 px-2 py-1 hover:bg-accent cursor-pointer text-sm transition-colors",
            isSelected && "bg-accent text-accent-foreground",
            "pl-" + (depth * 4 + 2)
          )}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => {
            if (node.type === 'folder') {
              toggleFolder(node.id);
            } else {
              setSelectedFile(node.id);
            }
          }}
        >
          {node.type === 'folder' && (
            <div className="w-4 h-4 flex items-center justify-center">
              {node.isOpen ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
            </div>
          )}
          <Icon className={cn("w-4 h-4", node.type === 'folder' ? "text-blue-400" : "text-muted-foreground")} />
          <span className="truncate">{node.name}</span>
        </div>
        
        {node.type === 'folder' && node.isOpen && node.children && (
          <div>
            {node.children.map(child => renderFileNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-64 h-full bg-sidebar border-r border-border flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-sidebar-foreground">Files</h3>
          <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
            <Plus className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* File Tree */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {files.map(file => renderFileNode(file))}
        </div>
      </ScrollArea>
    </div>
  );
};