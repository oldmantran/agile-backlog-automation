import * as React from "react"
import * as SwitchPrimitives from "@radix-ui/react-switch"

import { cn } from "../../lib/utils"

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      // Enhanced design tokens for Tron theme
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
      // Tron-themed switch states
      "data-[state=checked]:bg-primary data-[state=checked]:shadow-[0_0_10px_rgba(0,255,255,0.5)]",
      "data-[state=unchecked]:bg-input data-[state=unchecked]:border-border",
      className
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        // Enhanced thumb with Tron glow effect
        "pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-all duration-200",
        "data-[state=checked]:translate-x-5 data-[state=checked]:bg-primary-foreground data-[state=checked]:shadow-[0_0_8px_rgba(0,255,255,0.8)]",
        "data-[state=unchecked]:translate-x-0 data-[state=unchecked]:bg-muted-foreground"
      )}
    />
  </SwitchPrimitives.Root>
))
Switch.displayName = SwitchPrimitives.Root.displayName

export { Switch }
