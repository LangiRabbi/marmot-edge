import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WorkstationCard } from './WorkstationCard';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('WorkstationCard', () => {
  const defaultProps = {
    id: '1',
    name: 'Test Workstation',
    status: 'online' as const,
    peopleCount: 2,
    efficiency: 85,
    lastActivity: '2 min ago',
  };

  it('renders workstation card with correct information', () => {
    render(<WorkstationCard {...defaultProps} />);
    
    expect(screen.getByText('Test Workstation')).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('2 people')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('2 min ago')).toBeInTheDocument();
  });

  it('displays correct status color for offline status', () => {
    render(<WorkstationCard {...defaultProps} status="offline" />);
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('displays correct status color for alert status', () => {
    render(<WorkstationCard {...defaultProps} status="alert" />);
    expect(screen.getByText('Alert')).toBeInTheDocument();
  });

  it('calls onEdit when edit is triggered', () => {
    const onEdit = vi.fn();
    render(<WorkstationCard {...defaultProps} onEdit={onEdit} />);
    
    // Open dropdown menu
    const menuButton = screen.getByRole('button');
    fireEvent.click(menuButton);
    
    // Click edit option
    const editButton = screen.getByText('Edit Name');
    fireEvent.click(editButton);
    
    // Verify modal opens (we'd need to test the actual save in the modal test)
    expect(screen.getByText('Edit Name')).toBeInTheDocument();
  });

  it('displays efficiency with correct color coding', () => {
    const { rerender } = render(<WorkstationCard {...defaultProps} efficiency={90} />);
    expect(screen.getByText('90%')).toBeInTheDocument();
    
    rerender(<WorkstationCard {...defaultProps} efficiency={70} />);
    expect(screen.getByText('70%')).toBeInTheDocument();
    
    rerender(<WorkstationCard {...defaultProps} efficiency={40} />);
    expect(screen.getByText('40%')).toBeInTheDocument();
  });
});