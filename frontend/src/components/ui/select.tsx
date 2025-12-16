import React from "react"

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  placeholder?: string
  value?: string | number
  onValueChange?: (value: string) => void
  disabled?: boolean
  children: React.ReactNode
}

export interface SelectItemProps extends React.OptionHTMLAttributes<HTMLOptionElement> {
  value: string | number
  children: React.ReactNode
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(function Select(
  props,
  ref,
) {
  const { placeholder, value, onValueChange, disabled, children, style, ...rest } = props

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (onValueChange) onValueChange(e.target.value)
  }

  const containerStyle: React.CSSProperties = {
    position: "relative",
    width: "100%",
    minWidth: 0,
  }

  const baseStyle: React.CSSProperties = {
    width: "100%",
    height: "40px",
    padding: "8px 40px 8px 12px",
    fontSize: "14px",
    lineHeight: 1.2,
    color: "var(--chakra-colors-gray-800)",
    backgroundColor: "var(--chakra-colors-white)",
    border: "1px solid var(--chakra-colors-gray-200)",
    borderRadius: "8px",
    outline: "none",
    appearance: "none",
    WebkitAppearance: "none",
    MozAppearance: "none",
    boxShadow: "0 1px 2px rgba(16,24,40,0.06)",
    transition: "border-color 0.2s ease, box-shadow 0.2s ease",
    cursor: disabled ? "not-allowed" : "pointer",
    backgroundImage:
      "linear-gradient(to bottom, rgba(255,255,255,0), rgba(0,0,0,0))",
    ...style,
  }

  const iconStyle: React.CSSProperties = {
    position: "absolute",
    right: 12,
    top: "50%",
    transform: "translateY(-50%)",
    pointerEvents: "none",
    color: "var(--chakra-colors-gray-500)",
    fontSize: 12,
  }

  return (
    <div style={containerStyle}>
      <select
        ref={ref}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        style={baseStyle}
        {...rest}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {children}
      </select>
      <span aria-hidden style={iconStyle}>▼</span>
    </div>
  )
})

export const SelectItem = React.forwardRef<HTMLOptionElement, SelectItemProps>(
  function SelectItem(props, ref) {
    const { value, children, ...rest } = props
    return (
      <option ref={ref} value={value} {...rest}>
        {children}
      </option>
    )
  },
)
