import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Play, Save, Download, Copy, Eye, Code } from "lucide-react";

const sampleCode = `import React from 'react';
import { Button } from '@/components/ui/button';

export const App = () => {
  const [count, setCount] = React.useState(0);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent">
          Добро пожаловать в Lovable Clone
        </h1>
        <p className="text-lg text-muted-foreground">
          Создавайте красивые приложения с помощью AI
        </p>
        <div className="flex items-center gap-4 justify-center">
          <Button 
            onClick={() => setCount(count + 1)}
            className="bg-gradient-primary hover:opacity-80"
          >
            Счётчик: {count}
          </Button>
          <Button variant="outline">
            Начать разработку
          </Button>
        </div>
      </div>
    </div>
  );
};

export default App;`;

export const CodeEditor = () => {
  const [code, setCode] = useState(sampleCode);
  const [activeTab, setActiveTab] = useState("code");

  const lineCount = code.split('\n').length;

  return (
    <div className="flex-1 h-full bg-background flex flex-col">
      {/* Editor Header */}
      <div className="h-12 border-b border-border flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="text-xs">
            App.tsx
          </Badge>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs text-muted-foreground">Saved</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost">
            <Copy className="w-4 h-4 mr-1" />
            Copy
          </Button>
          <Button size="sm" variant="ghost">
            <Save className="w-4 h-4 mr-1" />
            Save
          </Button>
          <Button size="sm" className="bg-gradient-primary hover:opacity-80">
            <Play className="w-4 h-4 mr-1" />
            Run
          </Button>
        </div>
      </div>

      {/* Editor Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="w-fit mx-4 mt-2">
          <TabsTrigger value="code" className="flex items-center gap-2">
            <Code className="w-4 h-4" />
            Code
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Preview
          </TabsTrigger>
        </TabsList>

        <TabsContent value="code" className="flex-1 m-0">
          <div className="h-full flex">
            {/* Line Numbers */}
            <div className="w-12 bg-muted/30 border-r border-border p-2 text-right">
              <div className="text-xs text-muted-foreground font-mono leading-6">
                {Array.from({ length: lineCount }, (_, i) => (
                  <div key={i + 1}>{i + 1}</div>
                ))}
              </div>
            </div>

            {/* Code Area */}
            <ScrollArea className="flex-1">
              <div className="p-4">
                <pre className="text-sm font-mono leading-6 text-foreground whitespace-pre-wrap">
                  <code
                    className="language-tsx"
                    dangerouslySetInnerHTML={{
                      __html: code
                        .replace(/\b(import|export|const|let|var|function|return|if|else|for|while|class|interface|type)\b/g, '<span class="text-purple-400">$1</span>')
                        .replace(/\b(React|useState|useEffect)\b/g, '<span class="text-blue-400">$1</span>')
                        .replace(/"([^"]*)"/g, '<span class="text-green-400">"$1"</span>')
                        .replace(/'([^']*)'/g, '<span class="text-green-400">\'$1\'</span>')
                        .replace(/\/\/.*$/gm, '<span class="text-gray-500">$&</span>')
                        .replace(/\/\*[\s\S]*?\*\//g, '<span class="text-gray-500">$&</span>')
                    }}
                  />
                </pre>
              </div>
            </ScrollArea>
          </div>
        </TabsContent>

        <TabsContent value="preview" className="flex-1 m-0">
          <div className="h-full bg-preview-bg border border-border rounded-lg m-4 flex items-center justify-center">
            <div className="text-center space-y-4 p-8">
              <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Добро пожаловать в Lovable Clone
              </h1>
              <p className="text-lg text-muted-foreground">
                Создавайте красивые приложения с помощью AI
              </p>
              <div className="flex items-center gap-4 justify-center">
                <Button className="bg-gradient-primary hover:opacity-80">
                  Счётчик: 0
                </Button>
                <Button variant="outline">
                  Начать разработку
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};