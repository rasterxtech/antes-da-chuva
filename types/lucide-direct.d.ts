declare module 'lucide-react/dist/esm/icons/*.mjs' {
  import type {
    ForwardRefExoticComponent,
    RefAttributes,
    SVGProps,
  } from 'react';

  type DirectLucideIcon = ForwardRefExoticComponent<
    Omit<SVGProps<SVGSVGElement>, 'ref'> & RefAttributes<SVGSVGElement>
  >;

  const icon: DirectLucideIcon;
  export default icon;
}
