import React from "react"

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  placeholder?: string
  value?: string | number
  onValueChange?: (value: string) => void
  disabled?: boolean
  children: React.ReactNode
}

export interface SelectItemProps {
  value: string | number
  children: React.ReactNode
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  function Select(props, ref) {
    const { placeholder, value, onValueChange, disabled, children, ...rest } = props
    
    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (onValueChange) {
        onValueChange(e.target.value)
      }
    }
    
    return (
      <select
        ref={ref}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        style={{
          width: "100%",
          height: "40px",
          padding: "8px 12px",
          fontSize: "14px",
          border: "1px solid #e2e8f0",
          borderRadius: "6px",
          outline: "none",
        }}
        {...rest}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {children}
      </select>
    )
  },
)

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
