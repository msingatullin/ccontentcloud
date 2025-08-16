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

        {/* User Menu */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <div className="w-4 h-4 bg-gray-300 rounded border"></div>
            <span>Public</span>
          </div>
          
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <div className="w-4 h-4 bg-green-500 rounded flex items-center justify-center">
              <span className="text-xs text-white">S</span>
            </div>
            <span>Supabase</span>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                    M
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuItem className="flex cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem className="flex cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuItem className="flex cursor-pointer text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
};