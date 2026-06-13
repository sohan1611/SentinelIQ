import { useState, useEffect } from "react";

export function useStaggeredReveal(count: number, staggerDelay: number = 40, isLoaded: boolean) {
  const [styles, setStyles] = useState<React.CSSProperties[]>(
    Array(count).fill({ opacity: 0 })
  );
  const [showSkeletons, setShowSkeletons] = useState(!isLoaded);
  const [skeletonStyle, setSkeletonStyle] = useState<React.CSSProperties>({
    opacity: isLoaded ? 0 : 1,
  });

  useEffect(() => {
    if (isLoaded) {
      // Step 3: Skeletons fade out simultaneously (opacity 1 → 0, 150ms)
      setSkeletonStyle({
        opacity: 0,
        transition: "opacity 150ms var(--ease-in)",
      });

      // Wait for skeletons to fade out before showing content, OR do it simultaneously depending on requirement.
      // Wait, prompt: "Step 3: Skeletons fade out... Step 4: Module cards stagger in"
      // "Skeletons fade out: opacity 1 -> 0, 150ms. Content elements fade in: opacity 0 -> 1, 200ms ease-out. Stagger 40ms."
      const contentTimer = setTimeout(() => {
        setShowSkeletons(false);
        setStyles(
          Array.from({ length: count }).map((_, i) => ({
            opacity: 1,
            transition: `opacity 200ms var(--ease-out) ${i * staggerDelay}ms`,
          }))
        );
      }, 150); // delay content reveal until skeleton fades out
      
      return () => clearTimeout(contentTimer);
    } else {
      setShowSkeletons(true);
      setSkeletonStyle({ opacity: 1 });
      setStyles(Array(count).fill({ opacity: 0 }));
    }
  }, [isLoaded, count, staggerDelay]);

  return { styles, showSkeletons, skeletonStyle };
}
