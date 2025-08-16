import { Header } from "@/components/Header";
import { ChatSidebar } from "@/components/ChatSidebar";
import { FileExplorer } from "@/components/FileExplorer";
import { CodeEditor } from "@/components/CodeEditor";

const Editor = () => {
  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 flex overflow-hidden">
        <ChatSidebar />
        
        <div className="flex-1 flex">
          <FileExplorer />
          <CodeEditor />
        </div>
      </div>
    </div>
  );
};

export default Editor;