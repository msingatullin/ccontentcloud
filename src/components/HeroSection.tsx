import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Heart, Plus, ArrowUp } from "lucide-react";
import { useNavigate } from "react-router-dom";

export const HeroSection = () => {
  const [prompt, setPrompt] = useState("");
  const navigate = useNavigate();

  const handleSubmit = () => {
    if (prompt.trim()) {
      navigate("/editor");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gradient-hero flex items-center justify-center px-6">
      <div className="max-w-4xl mx-auto text-center space-y-8">
        {/* Main Heading */}
        <div className="space-y-4">
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white">
            Build something{" "}
            <span className="inline-flex items-center gap-2">
              <Heart className="w-12 h-12 md:w-16 md:h-16 lg:w-20 lg:h-20 text-primary fill-current" />
              Lovable
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-white/80 max-w-2xl mx-auto leading-relaxed">
            Create apps and websites by chatting with AI
          </p>
        </div>

        {/* Input Section */}
        <div className="max-w-3xl mx-auto">
          <div className="relative bg-hero-input border border-hero-input-border rounded-2xl p-4 shadow-xl backdrop-blur-sm">
            <Input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask Lovable to create an internal"
              className="bg-transparent border-0 text-lg placeholder:text-muted-foreground focus-visible:ring-0 pr-80"
            />
            
            {/* Input Actions */}
            <div className="absolute right-4 top-4 flex items-center gap-3">
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
              >
                <Plus className="w-4 h-4" />
              </Button>
              
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-3 text-muted-foreground hover:text-foreground flex items-center gap-1"
              >
                <span className="text-sm">📎</span>
                <span className="text-sm">Attach</span>
              </Button>
              
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-3 text-muted-foreground hover:text-foreground flex items-center gap-1"
              >
                <span className="text-sm">🌐</span>
                <span className="text-sm">Public</span>
              </Button>
              
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-3 text-muted-foreground hover:text-foreground flex items-center gap-1"
              >
                <span className="text-sm">💚</span>
                <span className="text-sm">Supabase</span>
              </Button>
              
              <Button
                onClick={handleSubmit}
                size="sm"
                className="h-8 w-8 p-0 bg-muted hover:bg-muted/80 rounded-full"
                disabled={!prompt.trim()}
              >
                <ArrowUp className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Helper Text */}
          <p className="text-sm text-white/60 mt-4">
            Press Enter to start building, or try asking for a specific type of website
          </p>
        </div>

        {/* Quick Start Examples */}
        <div className="flex flex-wrap justify-center gap-3 max-w-2xl mx-auto">
          {[
            "Create a modern portfolio",
            "Build a SaaS landing page", 
            "Make a restaurant website",
            "Design a dashboard"
          ].map((example) => (
            <Button
              key={example}
              variant="outline"
              size="sm"
              className="bg-white/10 border-white/20 text-white hover:bg-white/20 backdrop-blur-sm"
              onClick={() => setPrompt(example)}
            >
              {example}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};