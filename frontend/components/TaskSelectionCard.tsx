'use client';

interface Task {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  isSpecial?: boolean;
}

interface TaskSelectionCardProps {
  task: Task;
  onSelect: () => void;
  isGenerating?: boolean;
  disabled?: boolean;
}

export default function TaskSelectionCard({ task, onSelect, isGenerating = false, disabled = false }: TaskSelectionCardProps) {
  return (
    <button 
      onClick={onSelect}
      disabled={disabled || isGenerating}
      className={`luxury-card rounded-2xl p-8 sm:p-10 text-left group relative overflow-hidden transition-all duration-300 ${
        task.isSpecial ? 'col-span-full sm:col-span-2 lg:col-span-1' : ''
      } ${disabled || isGenerating ? 'opacity-50 cursor-not-allowed' : 'hover:transform hover:scale-105'}`}
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-yellow-500/10 to-transparent rounded-full blur-2xl"></div>
      <div className="relative">
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 ${
          task.isSpecial 
            ? 'gold-gradient' 
            : 'bg-gradient-to-br from-yellow-500/20 to-yellow-500/10 border border-yellow-500/20'
        }`}>
          <div className={task.isSpecial ? 'text-black' : 'gold-accent'}>
            {task.icon}
          </div>
        </div>
        <h3 className={`text-xl sm:text-2xl font-bold mb-3 flex items-center gap-2 ${
          task.isSpecial ? 'gold-accent' : 'text-foreground'
        }`} style={{ color: task.isSpecial ? undefined : 'var(--foreground)' }}>
          {task.title}
          {isGenerating && (
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
        </h3>
        <p className="text-sm sm:text-base font-light tracking-wide leading-relaxed" 
           style={{ color: 'var(--foreground-muted)' }}>
          {task.description}
        </p>
        {task.isSpecial && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium"
               style={{ 
                 background: 'rgba(212, 175, 55, 0.1)', 
                 color: 'var(--color-accent-gold)',
                 border: '1px solid rgba(212, 175, 55, 0.2)'
               }}>
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
            </svg>
            本番形式
          </div>
        )}
      </div>
    </button>
  );
}