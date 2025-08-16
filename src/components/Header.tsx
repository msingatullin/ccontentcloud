import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Settings, User, LogOut, Heart } from "lucide-react";

export const Header = () => {
  return (
    <header className="h-16 bg-background/95 backdrop-blur-sm sticky top-0 z-50 border-b border-border">
      <div className="h-full px-6 flex items-center justify-between max-w-7xl mx-auto">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Heart className="w-6 h-6 text-primary fill-current" />
            <span className="font-semibold text-xl text-foreground">Lovable</span>
          </div>
        </div>

        {/* Center Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <Button variant="ghost" className="text-muted-foreground hover:text-foreground font-medium">
            Community
          </Button>
          <Button variant="ghost" className="text-muted-foreground hover:text-foreground font-medium">
            Pricing
          </Button>
          <Button variant="ghost" className="text-muted-foreground hover:text-foreground font-medium">
            Enterprise
          </Button>
          <Button variant="ghost" className="text-muted-foreground hover:text-foreground font-medium">
            Learn
          </Button>
          <Button variant="ghost" className="text-muted-foreground hover:text-foreground font-medium">
            Launched
          </Button>
        </nav>

        {/* Auth Buttons */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="text-foreground hover:text-foreground/80 font-medium">
            Log in
          </Button>
          <Button className="bg-foreground text-background hover:bg-foreground/90 font-medium px-4">
            Get started
          </Button>
        </div>
      </div>
    </header>
  );
};