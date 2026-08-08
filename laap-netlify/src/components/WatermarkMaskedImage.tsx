import { cn } from '@/lib/utils';

interface WatermarkMaskedImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  maskPosition?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  maskWidth?: string;
  maskHeight?: string;
  containerClassName?: string;
}

export default function WatermarkMaskedImage({
  className,
  containerClassName,
  maskPosition = 'bottom-right',
  maskWidth = 'w-40',
  maskHeight = 'h-14',
  alt = '',
  ...props
}: WatermarkMaskedImageProps) {
  const positionClass = {
    'bottom-right': 'bottom-0 right-0 bg-gradient-to-tl',
    'bottom-left': 'bottom-0 left-0 bg-gradient-to-tr',
    'top-right': 'top-0 right-0 bg-gradient-to-bl',
    'top-left': 'top-0 left-0 bg-gradient-to-br',
  }[maskPosition];

  return (
    <div className={cn('relative overflow-hidden', containerClassName)}>
      <img
        className={cn('w-full h-full object-cover', className)}
        alt={alt}
        loading="lazy"
        decoding="async"
        {...props}
      />
      <div
        className={cn(
          'absolute pointer-events-none from-black/85 via-black/45 to-transparent',
          maskWidth,
          maskHeight,
          positionClass
        )}
        aria-hidden="true"
      />
    </div>
  );
}
