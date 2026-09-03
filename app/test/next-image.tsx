import type { ImgHTMLAttributes } from 'react';

type ImageProps = ImgHTMLAttributes<HTMLImageElement> & {
  fill?: boolean;
};

export default function Image({ fill: _fill, ...properties }: ImageProps) {
  void _fill;
  void properties;
  return null;
}
